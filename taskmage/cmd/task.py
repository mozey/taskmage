from sqlalchemy.sql import text
from taskmage.db import db, models
import datetime
from uuid import uuid4
from taskmage.exceptions import exceptions
from taskmage.response import Response
from taskmage import utils


def get_task(uuid):
    '''
    Lookup task using uuid or pointer id
    '''
    if type(uuid) == int:
        uuid = str(uuid)

    if uuid.find("-") > 0:
        return db.session.query(models.task).filter_by(uuid=uuid).first()

    pointer = db.session.query(models.pointer).filter_by(id=uuid).first()
    if pointer is not None:
        return pointer.task

    return None


def get_unused_pointer():
    '''
    Re-use an unused pointer row or add a new row.
    '''
    pointer = db.session.query(models.pointer) \
        .filter_by(task_uuid=None) \
        .first()
    # .orderBy("pointer.id")\
    if pointer is not None:
        return pointer
    else:
        pointer = models.pointer()
        db.session.add(pointer)
        return pointer


def add(description, project=None, urgency=None):
    mod(
        uuid=uuid4().__str__(),
        project=project,
        description=description,
        urgency=urgency
    )


def mod(uuid, description, project=None, urgency=None):
    '''
    Create or update a task
    '''
    response = Response();
    task = get_task(uuid)
    # Create the task if it doesn't exist
    if task is None:
        task = models.task()
        task.uuid = uuid

        # Get a pointer for this task
        pointer = get_unused_pointer()
        pointer.task_uuid = task.uuid

        task.project = project
        if urgency in ["h", "m", "l"]:
            task.urgency = urgency
        task.description = description
        db.session.add(task)
        response.message = "Creating task"

    else:
        # Update existing task
        if project and len(project.strip()) > 0:
            task.project = project
        if urgency is not None:
            if len(urgency) == 0:
                # Set urgency to null
                urgency = None
            if urgency in ["h", "m", "l"]:
                task.urgency = urgency
        if description and len(description.strip()) > 0:
            task.description = description
        response.message = "Updating existing task"

    db.session.commit()

    response.data = {
        "headers": ["modified", "project", "urgency", "description"],
        "rows": [[task.modified.__str__()[:16], task.project, task.urgency,
                  task.description]]
    }

    return response


def begin(task_uuid):
    response = Response()
    task = get_task(task_uuid)
    if task is None:
        raise exceptions.TaskNotFound

    # Create time sheet entry
    entry = models.entry()
    entry.uuid = uuid4().__str__()
    entry.sheet = utils.current_sheet()

    entry.start_time = utils.rounded_now()

    entry.end_time = None
    entry.task_uuid = task_uuid
    db.session.add(entry)

    db.session.commit()

    response.message = "Task started: {}".format(task.description)
    return response


def end(task_uuid):
    response = Response()
    entry = db.session.query(models.entry) \
        .filter_by(task_uuid=task_uuid, end_time=None) \
        .first()
    if entry is None:
        raise exceptions.TaskNotStarted

    entry.end_time = utils.rounded_now()

    db.session.commit()

    response.message = "Task stopped: {}".format(entry.task.description)
    return response


def done(task_uuid):
    response = Response()
    task = get_task(task_uuid)
    if task is None:
        raise exceptions.TaskNotFound

    # Stop time sheet entry for this task
    try:
        end(task.uuid)
    except exceptions.TaskNotStarted:
        pass

    # Set completed date on the task
    task.completed = utils.rounded_now()

    # Reset the pointer to this task
    pointer = db.session.query(models.pointer).filter_by(
        task_uuid=task.uuid).first()
    pointer.task_uuid = None

    db.session.commit()

    response.message = "Task completed: {}".format(task.description)
    return response


def entries(task_uuid):
    response = Response()
    entries = db.session.query(models.entry) \
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
            [entry.sheet, entry.start_time.__str__()[:16], end_time, hours])

    if total_hours is not None:
        rows.append([None, None, None, total_hours])

    db.session.commit()

    response.data = {
        "headers": ["sheet", "start", "end", "hours"],
        "rows": rows
    }
    return response


def ls(filters={"mods": {}}):
    response = Response()
    select = """distinct pointer.id as pointer_id, task.modified, task.project,
    task.urgency, task.description"""

    where = "1 = 1"
    for mod in filters["mods"]:
        if mod == "project":
            where += " and project like '{project}%'"
        elif mod == "urgency":
            where += " and urgency = '{urgency}'"
        elif mod == "description":
            where += " and description like '%{description}%'"
        elif mod == "completed":
            where += " and completed = '{completed}'"
        elif mod == "started":
            if filters["mods"]["started"]:
                select += ", max(entry.start_time) as start_time"
                where += " and entry.start_time is not null"
                where += " and entry.end_time is null"
        elif mod == "modified":
            if filters["mods"][mod] == "today":
                where += " and task.modified >= date('now', 'start of day', 'localtime')"
            else:
                raise exceptions.NotImplemented()

    if "completed" not in where:
        where += " and completed is null"

    where = where.format(**filters["mods"])

    sql = text("""
    select {select}
    from task
    join pointer on task.uuid = pointer.task_uuid
    left join entry on task.uuid = entry.task_uuid
    where {where}
    order by pointer_id desc
    limit 100
    """.format(select=select, where=where))

    cursor = db.session.execute(sql)
    task = cursor.fetchone();
    rows = []

    # Check task.pointer_id otherwise listing started tasks
    # throws and exception when there are no started tasks.
    while task is not None and task.pointer_id is not None:
        row = [task.pointer_id, task.modified[:16], task.project, task.urgency,
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
        task = cursor.fetchone();

    response.data = {
        "headers": ["id", "modified", "project", "urgency", "description",
                    "started", "hours"],
        "rows": rows
    }
    return response


def remove(task_uuid, prompt=True):
    """
    Prompt and then remove task and all related data
    """
    response = Response()
    task = get_task(task_uuid)
    if task is None:
        raise exceptions.TaskNotFound

    if prompt:
        yesno = input(
            "Delete everything for: {} ? y/n".format(task.description))
        if yesno == "n":
            print("Aborted")
            return

    entries = db.session.query(models.entry).filter_by(task_uuid=task.uuid)
    for entry in entries:
        db.session.delete(entry)

    task_tags = db.session.query(models.task_tag).filter_by(task_uuid=task.uuid)
    for task_tag in task_tags:
        db.session.delete(task_tag)

    pointer = db.session.query(models.pointer).filter_by(
        task_uuid=task.uuid).first()
    if pointer is not None:
        pointer.task_uuid = None

    db.session.delete(task)
    db.session.commit()

    response.message = "Task removed: {}".format(task.description)
    return response
