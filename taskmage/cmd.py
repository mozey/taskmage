from sqlalchemy.sql import text
from taskmage.db import db, models
from datetime import datetime
from uuid import uuid4
from taskmage.exceptions import exceptions
from tabulate import tabulate

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
    pointer = db.session.query(models.pointer)\
        .filter_by(task_uuid=None)\
        .first()
        # .orderBy("pointer.id")\
    if pointer is not None:
        return pointer
    else:
        pointer = models.pointer()
        db.session.add(pointer)
        return pointer


def add_task(description, project=None, urgency=None):
    touch_task(
        uuid=uuid4().__str__(),
        project=project,
        description=description,
        urgency=urgency
    )


def touch_task(uuid, description, project=None, urgency=None):
    '''
    Create or update a task
    '''
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
        print("Creating task")

    else:
        # Update existing task
        task.project = project
        if urgency is not None:
            if len(urgency) == 0:
                # Set urgency to null
                urgency = None
            if urgency in ["h", "m", "l"]:
                task.urgency = urgency
        task.description = description
        print("Updating existing task")

    db.session.commit()


def start_task(task_uuid):
    task = get_task(task_uuid)
    if task is None:
        raise exceptions.TaskNotFound

    # Create time sheet entry
    entry = models.entry()
    entry.uuid = uuid4().__str__()
    entry.sheet = current_sheet()
    entry.start_time = datetime.utcnow()
    entry.end_time = None
    entry.task_uuid = task_uuid
    db.session.add(entry)

    print("Task started: {}".format(task.description))

    db.session.commit()


def end_task(task_uuid):
    entry = db.session.query(models.entry)\
        .filter_by(task_uuid=task_uuid, end_time=None)\
        .first()
    if entry is None:
        raise exceptions.TaskNotStarted

    entry.end_time = datetime.utcnow()

    print("Task stopped: {}".format(entry.task.description))

    db.session.commit()


def complete_task(task_uuid):
    task = get_task(task_uuid)
    if task is None:
        raise exceptions.TaskNotFound

    # Stop time sheet entry for this task
    try:
        end_task(task.uuid)
    except exceptions.TaskNotStarted:
        pass

    # Set completed date on the task
    task.completed = datetime.utcnow()

    # Reset the pointer to this task
    pointer = db.session.query(models.pointer).filter_by(task_uuid=task.uuid).first()
    pointer.task_uuid = None

    db.session.commit()


def remove_task(task_uuid):
    """
    Delete the task if it has no timesheet entries, otherwise complete it.
    """
    task = get_task(task_uuid)
    if task is None:
        raise exceptions.TaskNotFound

    entries = db.session.query(models.entry).filter_by(task_uuid=task.uuid).count()
    if entries > 0:
        complete_task(task_uuid)
    else:
        # TODO Prompt before deleting
        db.session.delete(task)

    db.session.commit()


def current_sheet():
    '''
    Current timesheet is the current month by default
    '''
    return datetime.strftime(datetime.now(), "%Y-%m")


def timesheet_report(sheet, project=None):
    print(sheet, project)


def tasks(filters={"mods": {}}):
    select = """distinct pointer.id as pointer_id, task.project, task.urgency,
    task.description"""

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

    while task is not None:
        row = [task.pointer_id, task.project, task.urgency, task.description]
        if "start_time" in task._keymap and task.start_time is not None:
            start_time = task.start_time[:19]
            row.append(start_time)

            now = datetime.utcnow()
            elapsed = now - start_time
            seconds_elapsed = elapsed.total_seconds()
            row.append(seconds_elapsed)

        rows.append(row)
        task = cursor.fetchone();

    # List the task
    print(tabulate(rows, headers=["id", "project", "urgency", "description", "started", "elapsed"]))


