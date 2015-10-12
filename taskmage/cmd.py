from taskmage.db import db, models
from datetime import datetime
from uuid import uuid1

def add_entry(uuid, project, description):
    with db.get_session() as session:

        # Create the task if it doesn't exist
        task = session.query(models.Task).filter_by(uuid=uuid).first()
        if task is None:
            print("Creating task")
            task = models.Task()
            task.uuid = uuid
            task.project = project
            task.description = description
            session.add(task)

        else:
            print("Existing task")
            print(task)

        # Create time sheet entry
        entry = models.Entry()
        entry.uuid = uuid1().__str__()
        entry.sheet = current_sheet()
        entry.start_time = datetime.utcnow()
        entry.end_time = None
        entry.task_uuid = task.uuid
        session.add(entry)
        print(entry)

        session.commit()


def current_sheet():
    return "2015-10 October"


def report(sheet):
    print(sheet)


def tasks(filter):
    with db.get_session() as session:
        tasks = session.query(models.Task).all()
        if len(tasks) > 0:
            print("Listing tasks")
            for task in tasks:
                print("Task: ", task)
        else:
            print("No tasks")
