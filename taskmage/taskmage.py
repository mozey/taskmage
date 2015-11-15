# -*- coding: utf-8 -*-


"""taskmage.taskmage: provides entry point main()."""


__version__ = "0.1.4"



import sys
import os, time, shutil, glob, datetime

# from taskmage import config
# config.echo = True

from taskmage.db import db, models
from taskmage import cmd
from taskmage import args


def rolling_backup():
    """
    Create db backup if previous backup is older than interval
    :return:
    """
    # TODO Make interval and backups_to_keep configurable
    backups_to_keep = 3
    interval = 60 * 30 # 30 minutes

    timestamp_format = "%Y-%m-%d-%H-%M-%S"

    backup_files = glob.glob("{}.bak-*".format(db.db_path))
    backup_files.sort()
    backup_files_len = len(backup_files)
    last_backup = backup_files.pop()
    last_backup_timestamp = last_backup[-19:]

    modified = time.mktime(
        datetime.datetime.strptime(last_backup_timestamp, timestamp_format).timetuple()
    )
    now = datetime.datetime.utcnow()
    diff = now.timestamp() - modified

    new_backup = "{}.bak-{}".format(
        db.db_path,
        datetime.datetime.strftime(now, timestamp_format)
    )

    if backups_to_keep > 0 and backup_files_len > backups_to_keep:
        for i in range(backup_files_len - backups_to_keep):
            os.remove(backup_files[i])

    if diff > interval:
        shutil.copyfile(db.db_path, new_backup)
        print("Last backup was {} hours ago, new backup created".format(round(diff/60/60, 2)))


def print_help():
    # TODO Add help text
    print("Python command line TODO manager with time tracking")
    exit(0)


def main():
    rolling_backup()

    # Create or update database schema
    models.create_all()

    with db.get_session() as session:
        db.session = session

    first_arg = ""
    if len(sys.argv) > 1:
        first_arg = sys.argv[1]
    if first_arg.startswith("h"):
        print_help()

    filters, command, mods, description = args.parse(sys.argv)
    # print(filters, command, mods, description)

    response = None

    if command == "ls":
        if len(filters["pointers"]) > 0:
            # List timesheet entries
            for pointer_id in filters["pointers"]:
                task = cmd.get_task(pointer_id)
                response = cmd.list_entries(task.uuid)

        else:
            # List tasks
            if "description" not in filters["mods"] and description is not None:
                filters["mods"]["description"] = description
            response = cmd.tasks(filters)

    elif command == "timesheet":
        response = cmd.timesheet_report(filters)

    elif command == "add":
        params = {"description": description}
        if "project" in mods:
            params["project"] = mods["project"]
        if "urgency" in mods:
            params["urgency"] = mods["urgency"]
        response = cmd.add_task(**params)

    elif command == "mod":
        args.pointer_required(filters)
        for pointer_id in filters["pointers"]:
            params = {
                "uuid": pointer_id,
                "description": description
            }
            if "project" in mods:
                params["project"] = mods["project"]
            if "urgency" in mods:
                params["urgency"] = mods["urgency"]
            response = cmd.touch_task(**params)

    elif command == "done":
        args.pointer_required(filters)
        for pointer_id in filters["pointers"]:
            task = cmd.get_task(pointer_id)
            response = cmd.complete_task(task.uuid)

    elif command == "started":
        filters["mods"]["started"] = True
        response = cmd.tasks(filters)

    elif command == "begin":
        args.pointer_required(filters)
        for pointer_id in filters["pointers"]:
            task = cmd.get_task(pointer_id)
            response = cmd.start_task(task.uuid)

    elif command == "end":
        args.pointer_required(filters)
        for pointer_id in filters["pointers"]:
            task = cmd.get_task(pointer_id)
            response = cmd.end_task(task.uuid)

    elif command == "remove":
        args.pointer_required(filters)
        for pointer_id in filters["pointers"]:
            task = cmd.get_task(pointer_id)
            response = cmd.remove_task(task.uuid)

    else:
        print_help()

    if response:
        response.print()