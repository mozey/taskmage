from taskmage.db import db, models
from datetime import datetime
from uuid import uuid4

def get_task(uuid):
    '''
    Lookup task using uuid or id
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


def touch_task(uuid, project, description, priority=None):
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
        task.priority = priority
        task.description = description
        db.session.add(task)
        print("Creating task")

    else:
        # Update existing task
        task.project = project
        if priority is not None:
            if len(priority) == 0:
                # Set priority to null
                priority = None
            task.priority = priority
        task.description = description
        print("Updating existing task")

    db.session.commit()


def start_task(task_uuid):
    task = get_task(task_uuid)
    if task is None:
        raise Exception("Unknown task")

    # Create time sheet entry
    entry = models.entry()
    entry.uuid = uuid4().__str__()
    entry.sheet = current_sheet()
    entry.start_time = datetime.utcnow()
    entry.end_time = None
    entry.task_uuid = task_uuid
    db.session.add(entry)

    print("Entry started for task {}".format(task.description))

    db.session.commit()


def stop_task(task_uuid):
    entry = db.session.query(models.entry).filter_by(task_uuid=task_uuid).first()
    if entry is None:
        raise Exception("Task not started")

    entry.end_time = datetime.utcnow()

    print("Entry started for task {}".format(entry.task.description))

    db.session.commit()


def complete_task(task_uuid):
    task = get_task(task_uuid)
    if task is None:
        raise Exception("Unknown task")

    # TODO Check if task has active timesheet entry and stop it

    # TODO Set completed date on the task

    # TODO Set pointer.task_uuid = null


def current_sheet():
    '''
    Current timesheet is the current month by default
    '''
    return datetime.strftime(datetime.now(), "%Y-%M")


def timesheet_report(sheet, project=None):
    print(sheet, project)


def tasks(filter=""):
    print(filter)
    tasks = db.session.query(models.task).all()
    if len(tasks) > 0:
        print("Listing tasks")
        for task in tasks:
            print(task)
    else:
        print("No tasks")
