from sqlalchemy.sql import text
from taskmage.db import db
from taskmage.response import Response
from taskmage import utils
from taskmage.exceptions import exceptions


def report(filters):
    response = Response()

    select = """
    pointer.id as pointer_id, task.project as task_project,
    task.description as task_description, task.completed as task_completed,
    sum(strftime('%s', entry.end_time) - strftime('%s', entry.start_time)) as seconds
    """

    where = "1 = 1"
    for mod in filters["mods"]:
        if mod == "project":
            where += " and project like :project"
            # Match start
            filters["mods"][mod] += "%"

        elif mod == "description":
            where += " and description like :description"
            # Match anywhere
            filters["mods"][mod] = "%{}%".format(filters["mods"][mod])

        elif mod == "sheet":
            where += " and sheet like :sheet"
            # Match start
            filters["mods"][mod] += "%"

        elif mod == "modified":
            if filters["mods"][mod] == "today":
                where += " and task.modified >= date('now', 'start of day', 'localtime')"
            else:
                raise exceptions.NotImplemented()

    # Using Textual SQL
    # http://docs.sqlalchemy.org/en/latest/core/tutorial.html#using-textual-sql
    sql = text("""
    select {select}
    from task
    join pointer on task.uuid = pointer.task_uuid
    join entry on task.uuid = entry.task_uuid
    where {where}
    group by task.uuid
    order by task.uuid;
    """.format(select=select, where=where))

    rows = []
    sql = sql.bindparams(**filters["mods"])
    cursor = db.session.execute(sql)
    entry = cursor.fetchone();

    while entry is not None:
        completed = None
        if entry.task_completed is not None:
            completed = entry.task_completed[:16]
        rows.append(
            [entry.pointer_id, entry.task_project, entry.task_description,
             completed, utils.time_from_seconds(entry.seconds)])
        entry = cursor.fetchone();

    response.data = {
        "headers": ["id", "project", "description", "completed", "hours"],
        "rows": rows
    }
    return response
