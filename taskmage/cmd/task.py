from sqlalchemy.sql import text
from sqlalchemy import orm
from taskmage.db import db, models
import datetime
from uuid import uuid4
from taskmage.exceptions import exceptions
from taskmage.response import Response
from taskmage import utils


class Task:
    def __init__(self):
        with db.get_session() as session:
            self.session = session

    def get_task(self, uuid: str) -> models.task:
        """
        Lookup task using uuid or pointer id
        :param uuid:
        :return:
        """
        if uuid.find("-") > 0:
            return self.session.query(models.task).filter_by(uuid=uuid).first()

        pointer = self.session.query(models.pointer).filter_by(id=uuid).first()
        if pointer is not None:
            return pointer.task

        return None

    def get_tag(self, tag: str) -> models.tag:
        return self.session.query(models.tag).filter_by(tag=tag).first()

    def get_unused_pointer(self):
        """
        Re-use an unused pointer row or add a new row.
        """
        pointer = self.session.query(models.pointer) \
            .filter_by(task_uuid=None) \
            .first()
        # .orderBy("pointer.id")\
        if pointer is not None:
            return pointer
        else:
            pointer = models.pointer()
            self.session.add(pointer)
            return pointer

    def add(self, description, project=None, urgency=None, tags=None):
        self.mod(
                uuid=uuid4().__str__(),
                project=project,
                description=description,
                urgency=urgency,
                tags=tags,
        )

    def add_tag(self, task, tag):
        # import pdb; pdb.set_trace()
        tag = self.get_tag(tag)
        if tag is None:
            tag = models.tag()
            tag.tag = tag
            self.session.add(tag)
            self.session.commit()

        task_tag = self.session.query(models.task_tag)\
            .filter_by(task_uuid=task.uuid, tag_uuid=tag.uuid)\
            .first()

        if task_tag is None:
            task_tag = models.task_tag()
            task_tag.task_uuid = task.uuid
            task_tag.tag_uuid = tag.uuid

            self.session.add(task_tag)
            self.session.commit()

    def remove_tag(self, task, tag):
        task_tags = self.session.query(models.task_tag) \
            .filter_by(task_uuid=task.uuid, tag_uuid=tag.uuid)

        for task_tag in task_tags:
            self.session.delete(task_tag)

        self.session.commit()

    def mod(self, uuid, description, project=None, urgency=None, tags=None):
        """
        Create or update a task
        :param uuid:
        :param description:
        :param project:
        :param urgency:
        :param tags:
        :return:
        """
        response = Response()

        if tags is None:
            tags = []

        task = self.get_task(uuid)
        # Create the task if it doesn't exist
        if task is None:
            task = models.task()
            task.uuid = uuid

            # Get a pointer for this task
            pointer = self.get_unused_pointer()
            pointer.task_uuid = task.uuid

            task.project = project
            if urgency in models.urgency:
                task.urgency = urgency
            elif urgency is not None:
                raise exceptions.InvalidValueForUrgency(urgency)
            task.description = description
            self.session.add(task)
            response.message = "Creating task"

        else:
            # Update existing task
            if project and len(project.strip()) > 0:
                task.project = project
            if urgency in models.urgency:
                task.urgency = urgency
            elif urgency is not None:
                raise exceptions.InvalidValueForUrgency(urgency)
            if description and len(description.strip()) > 0:
                task.description = description
            response.message = "Updating existing task"

        # Update tags
        for tag in tags:
            if tag[:1] == "+":
                self.add_tag(task, tag[1:])

            elif tag[:1] == "-":
                self.remove_tag(task, tag[1:])

        self.session.commit()

        response.data = {
            "headers": ["modified", "project", "urgency", "description"],
            "rows": [[task.modified.__str__()[:16], task.project, task.urgency,
                      task.description]]
        }

        return response

    def start(self, task_uuid):
        response = Response()
        task = self.get_task(task_uuid)
        if task is None:
            raise exceptions.TaskNotFound

        # Create time sheet entry
        entry = models.entry()
        entry.uuid = uuid4().__str__()
        entry.sheet = utils.current_sheet()

        entry.start_time = utils.rounded_now()

        entry.end_time = None
        entry.task_uuid = task_uuid
        self.session.add(entry)

        self.session.commit()

        response.message = "Task started: {}".format(task.description)
        return response

    def stop(self, task_uuid):
        response = Response()
        entry = self.session.query(models.entry) \
            .filter_by(task_uuid=task_uuid, end_time=None) \
            .first()
        if entry is None:
            raise exceptions.TaskNotStarted

        entry.end_time = utils.rounded_now()

        self.session.commit()

        response.message = "Task stopped: {}".format(entry.task.description)
        return response

    def done(self, task_uuid):
        response = Response()
        task = self.get_task(task_uuid)
        if task is None:
            raise exceptions.TaskNotFound

        # Stop time sheet entry for this task
        try:
            self.stop(task.uuid)
        except exceptions.TaskNotStarted:
            pass

        # Set completed date on the task
        task.completed = utils.rounded_now()

        # Reset the pointer to this task
        pointer = self.session.query(models.pointer).filter_by(
                task_uuid=task.uuid).first()
        pointer.task_uuid = None

        self.session.commit()

        response.message = "Task completed: {}".format(task.description)
        return response

    def entries(self, task_uuid):
        response = Response()
        entries = self.session.query(models.entry) \
            .filter_by(task_uuid=task_uuid)

        rows = []
        total_hours = None
        for entry in entries:
            end_time = None
            hours = None
            if entry.end_time is not None:
                end_time = entry.end_time.__str__()[:16]
                hours = entry.end_time - entry.start_time
                if total_hours is None:
                    total_hours = datetime.timedelta()
                total_hours += hours
            rows.append(
                    [entry.sheet, entry.start_time.__str__()[:16], end_time,
                     hours])

        if total_hours is not None:
            rows.append([None, None, None, total_hours])

        self.session.commit()

        response.data = {
            "headers": ["sheet", "start", "end", "hours"],
            "rows": rows
        }
        return response

    def ls(self, filters=None):
        response = Response()

        if filters is None:
            filters = {"mods": {}}

        select = """distinct pointer.id as pointer_id, task.modified, task.project,
        task.urgency, task.description"""

        params = {}
        where = "1 = 1"
        for mod in filters["mods"]:
            if mod == "project":
                where += " and project like :project"
                # Match start
                filters["mods"][mod] += "%"
                params[mod] = filters["mods"][mod]

            elif mod == "urgency":
                where += " and urgency = :urgency"
                params[mod] = filters["mods"][mod]

            elif mod == "description":
                where += " and description like :description"
                # Match anywhere
                filters["mods"][mod] = "%{}%".format(filters["mods"][mod])
                params[mod] = filters["mods"][mod]

            elif mod == "completed":
                where += " and completed = :completed"
                params[mod] = filters["mods"][mod]

            elif mod == "started":
                if filters["mods"]["started"]:
                    select += ", max(entry.start_time) as start_time"
                    where += " and entry.start_time is not null"
                    where += " and entry.end_time is null"

            elif mod == "modified":
                if filters["mods"][mod] == "today":
                    where += " and task.modified >= \
                    date('now', 'start of day', 'localtime')"
                else:
                    raise exceptions.NotImplemented()

        if "completed" not in where:
            where += " and completed is null"

        sql = text("""
        select {select}
        from task
        join pointer on task.uuid = pointer.task_uuid
        left join entry on task.uuid = entry.task_uuid
        where {where}
        order by pointer.id desc
        limit 100
        """.format(select=select, where=where))

        sql = sql.bindparams(**params)
        cursor = self.session.execute(sql)
        task = cursor.fetchone()
        rows = []

        # Check task.pointer_id otherwise listing started tasks
        # throws and exception when there are no started tasks.
        while task is not None and task.pointer_id is not None:
            row = [task.pointer_id, task.modified[:16], task.project,
                   task.urgency,
                   task.description]
            if "start_time" in task._keymap and task.start_time is not None:
                start_time = task.start_time[:19]
                row.append(start_time)

                now = datetime.datetime.utcnow()
                elapsed = now - datetime.datetime.strptime(start_time,
                                                           db.timestamp_format)
                hours_elapsed = utils.time_from_seconds(elapsed.total_seconds())
                row.append(hours_elapsed)

            rows.append(row)
            task = cursor.fetchone()

        response.data = {
            "headers": ["id", "modified", "project", "urgency", "description",
                        "started", "hours"],
            "rows": rows
        }
        return response

    def remove(self, task_uuid, prompt=True):
        """
        Prompt and then remove task and all related data
        :param task_uuid:
        :param prompt:
        :return:
        """
        response = Response()
        task = self.get_task(task_uuid)
        if task is None:
            raise exceptions.TaskNotFound

        if prompt:
            yesno = input(
                    "Delete everything for: {} ? y/n ".format(task.description))
            if yesno == "n":
                print("Aborted")
                return

        entries = self.session.query(models.entry).filter_by(
            task_uuid=task.uuid)
        for entry in entries:
            self.session.delete(entry)

        task_tags = self.session.query(models.task_tag).filter_by(
            task_uuid=task.uuid)
        for task_tag in task_tags:
            self.session.delete(task_tag)

        pointer = self.session.query(models.pointer).filter_by(
                task_uuid=task.uuid).first()
        if pointer is not None:
            pointer.task_uuid = None

        self.session.delete(task)
        self.session.commit()

        response.message = "Task removed: {}".format(task.description)
        return response

    def list_entries(self, task_uuid: str):
        response = Response()
        entries = self.session.query(models.entry) \
            .filter_by(task_uuid=task_uuid)

        rows = []
        total_hours = None
        for entry in entries:
            assert isinstance(entry, models.entry)
            end_time = None
            hours = None
            if entry.end_time is not None:
                end_time = entry.end_time.__str__()[:16]
                hours = entry.end_time - entry.start_time
                if total_hours is None:
                    total_hours = hours
                else:
                    total_hours += hours
            rows.append([entry.sheet, entry.start_time.__str__()[:16], end_time,
                         hours])

        rows.append([None, None, None, total_hours])

        self.session.commit()

        response.data = {
            "headers": ["sheet", "start", "end", "hours"],
            "rows": rows
        }
        return response
