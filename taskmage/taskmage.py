# -*- coding: utf-8 -*-


"""taskmage.taskmage: provides entry point main()."""


__version__ = "0.0.1"


import argparse
from collections import OrderedDict
from taskmage.db import db, models

parser = argparse.ArgumentParser(description="Time tracking for taskwarrior")


# Main commands
# At least one of the main command are required
# http://stackoverflow.com/a/4466258/639133
main_commands = parser.add_mutually_exclusive_group(required=True)
main_commands.add_argument("-r", '--report', nargs="?", const="latest", help='Time sheet report, use latest sheet by default')
main_commands.add_argument("-s", '--sheets', nargs="?", const="all", help='List time sheets')
main_commands.add_argument("-t", '--tasks', nargs="?", const="all", help='List all tasks')
add_command={"task": OrderedDict({"uuid": 0, "project": 1, "description": 2})}
main_commands.add_argument("-a", '--add', nargs=3, help='Add entry: {}'.format(" ".join(["task." + k for k in add_command["task"]])))


def main():
    # Parse command line args
    args = parser.parse_args()

    # print("Executing bootstrap version %s." % __version__)
    # print("List of argument strings: %s" % sys.argv[1:])

    # Create or update database schema
    models.create_all()

    with db.get_session() as session:
        db.session = session

        if args.report is not None:
            from taskmage.cmd import report
            report(args.report)

        if args.tasks is not None:
            from taskmage.cmd import tasks
            tasks(args.tasks)

        if args.add is not None:
            from taskmage.cmd import add_entry
            add_entry_args = {}
            for key in add_command["task"]:
                add_entry_args[key] = args.add[add_command["task"][key]]
            # Expand dict to function args:
            # http://stackoverflow.com/a/7745986/639133
            add_entry(**add_entry_args)
