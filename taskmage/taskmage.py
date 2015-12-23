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
from taskmage.exceptions import exceptions


def rolling_backup():
    """
    Create db backup if previous backup is older than interval
    :return:
    """
    # TODO Make interval and backups_to_keep configurable
    backups_to_keep = 3
    interval = 60 * 30  # 30 minutes

    timestamp_format = "%Y-%m-%d-%H-%M-%S"

    backup_files = glob.glob("{}.bak-*".format(db.db_path))
    backup_files.sort()
    backup_files_len = len(backup_files)
    last_backup = backup_files.pop()
    last_backup_timestamp = last_backup[-19:]

    modified = time.mktime(
        datetime.datetime.strptime(last_backup_timestamp,
                                   timestamp_format).timetuple()
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
        print("Last backup was {} hours ago, new backup created".format(
            round(diff / 60 / 60, 2)))


def print_help():
    # TODO Add help text
    print("Python command line TODO manager with time tracking")
    print("")
    print("commands")
    print("     ls")
    print("     timesheet")
    print("     add")
    print("     mod")
    print("     done")
    print("     start")
    print("     stop")
    print("     remove")
    print("")
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
    print("...................................................................")
    print("debug:")
    print(filters, command, mods, description)
    print("...................................................................")
    print()

    response = None

    if command is None:
        print_help()

    elif command[0] == "ls":
        if len(filters["pointers"]) > 0:
            # List timesheet entries
            for pointer_id in filters["pointers"]:
                task = cmd.task.get_task(pointer_id)
                response = cmd.task.list_entries(task.uuid)

        else:
            # List tasks
            if "description" not in filters["mods"] and description is not None:
                filters["mods"]["description"] = description
            response = cmd.task.ls(filters)

    elif command[0] == "timesheet":
        response = cmd.timesheet.report(filters)

    elif command[0] == "add":
        params = {"description": description}

        if "project" in mods:
            if len(mods["project"]) > 1:
                raise exceptions.ModMustHaveOneValue('"project"')
            params["project"] = mods["project"][0]

        if "urgency" in mods:
            if len(mods["project"]) > 1:
                raise exceptions.ModMustHaveOneValue('"urgency"')
            params["urgency"] = mods["urgency"][0]

        if "tag" in mods:
            params["tags"] = mods["tag"]

        response = cmd.task.add(**params)

    elif command[0] == "mod":
        args.pointer_required(filters)
        for pointer_id in filters["pointers"]:
            params = {
                "uuid": pointer_id,
                "description": description
            }

            if "project" in mods:
                params["project"] = mods["project"][0]

            if "urgency" in mods:
                params["urgency"] = mods["urgency"][0]

            if "tag" in mods:
                params["tags"] = mods["tag"]

            response = cmd.task.mod(**params)

    elif command[0] == "done":
        args.pointer_required(filters)
        for pointer_id in filters["pointers"]:
            task = cmd.task.get_task(pointer_id)
            response = cmd.task.done(task.uuid)

    elif command == ["start", "stop"]:
        # Stop or start task if pointer given
        if len(filters["pointers"]) > 0:
            for pointer_id in filters["pointers"]:
                task = cmd.task.get_task(pointer_id)
                try:
                    # Try to stop this task
                    response = cmd.task.stop(task.uuid)
                except exceptions.TaskNotStarted:
                    # Task not started, start it
                    response = cmd.task.start(task.uuid)
        else:
            # List started tasks
            filters["mods"]["started"] = True
            response = cmd.task.ls(filters)

    elif command[0] == "remove":
        args.pointer_required(filters)
        for pointer_id in filters["pointers"]:
            task = cmd.task.get_task(pointer_id)
            response = cmd.task.remove(task.uuid)

    else:
        print_help()

    if response:
        response.print()

    print()
