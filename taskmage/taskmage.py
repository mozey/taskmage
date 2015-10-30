# -*- coding: utf-8 -*-


"""taskmage.taskmage: provides entry point main()."""


__version__ = "0.0.1"

import sys

# from taskmage import config
# config.echo = True

from taskmage.db import db, models
from taskmage import cmd
from taskmage.exceptions import exceptions
from taskmage import args

def main():
    # Create or update database schema
    models.create_all()

    with db.get_session() as session:
        db.session = session

    first_arg = ""
    if len(sys.argv) > 1:
        first_arg = sys.argv[1]
    if first_arg.startswith("h"):
        print("Python command line TODO manager with time tracking")
        exit(0)

    filters, command, mods, description = args.parse(sys.argv)
    print(filters, command, mods, description)

    if command is None or command == "ls":
        cmd.tasks(filters)

    elif command == "add":
        params = {"description": description}
        if "project" in mods:
            params["project"] = mods["project"]
        if "urgency" in mods:
            params["urgency"] = mods["urgency"]
        cmd.add_task(**params)

    elif command == "mod":
        if "pointers" in filters:
            for pointer_id in filters["pointers"]:
                params = {
                    "uuid": pointer_id,
                    "description": description
                }
                if "project" in mods:
                    params["project"] = mods["project"]
                if "urgency" in mods:
                    params["urgency"] = mods["urgency"]
                cmd.touch_task(**params)
        else:
            raise exceptions.FilterRequired("Id")

    elif command == "done":
        if "pointers" in filters:
            for pointer_id in filters["pointers"]:
                task = cmd.get_task(pointer_id)
                cmd.complete_task(task.uuid)
        else:
            raise exceptions.FilterRequired("Id")

    elif command == "started":
        filters["mods"]["started"] = True
        cmd.tasks(filters)

    elif command == "begin":
        if "pointers" in filters:
            for pointer_id in filters["pointers"]:
                task = cmd.get_task(pointer_id)
                cmd.start_task(task.uuid)
        else:
            raise exceptions.FilterRequired("Id")

    elif command == "end":
        if "pointers" in filters:
            for pointer_id in filters["pointers"]:
                task = cmd.get_task(pointer_id)
                cmd.end_task(task.uuid)
        else:
            raise exceptions.FilterRequired("Id")

    elif command == "remove":
        if "pointers" in filters:
            for pointer_id in filters["pointers"]:
                task = cmd.get_task(pointer_id)
                cmd.end_task(task.uuid)
        else:
            raise exceptions.FilterRequired("Id")

    else:
        # Listing tasks is the default action.

        # Being a bit lazy here, instead of making the regex parsing smarter
        # we assume the "command" forms part of the description filter.
        composite_description = ""
        if command is not None:
            composite_description += command
        if description is not None:
            composite_description += " " + description

        # Overwrite the description mod when using this form.
        filters["mods"]["description"] = composite_description

        cmd.tasks(filters)
