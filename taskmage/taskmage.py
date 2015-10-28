# -*- coding: utf-8 -*-


"""taskmage.taskmage: provides entry point main()."""


__version__ = "0.0.1"

import sys
from taskmage.db import db, models
import re
from taskmage import cmd
from taskmage.exceptions import exceptions

def expand_mod(arg):
    args = arg.split(":")
    key = args[0]
    value = args[1]
    pattern = re.compile("^{}.*$".format(key))
    pattern_match = pattern.match

    found_match = None
    for mod in models.mods:
        match = pattern_match(mod)
        if match is not None:
            if found_match is None:
                found_match = match
            else:
                raise exceptions.ModAmbiguous

    if found_match is not None:
        return [found_match.string, value]

    raise exceptions.ModNotFound()


def get_params():
    '''
    Command must consist of word characters only
    Filters => 1 or 1,2 or +tag or attr:value
    Mods => key:value
    '''

    filters = {}
    filters["mods"] = {}
    filters["pointers"] = []

    command = None
    mods = {}
    description = None

    mod_pattern = re.compile('^\w+:\w+$')
    pointer_pattern = re.compile('^\d+$')
    # TODO range must support 1,2,3 or 1-3
    # range_pattern = re.compile('^(\d+,\d+)$')

    for arg in sys.argv[1:]:

        if command is None:
            command_pattern = re.compile('^[A-Za-z]*$')
            match = command_pattern.match(arg)

        if command is not None:
            # Everything after the command is either mods or description
            if mod_pattern.match(arg):
                mod = expand_mod(arg)
                mods[mod[0]] = mod[1]

            else:
                if description is None:
                    description = "{}".format(arg)
                else:
                    description += " {}".format(arg)

        elif match is not None:
            command = match.string

        else:
            # Everything before the command goes into filters
            if mod_pattern.match(arg):
                mod = expand_mod(arg)
                filters["mods"][mod[0]] = mod[1]

            elif pointer_pattern.match(arg):
                filters["pointers"].append(arg)

            else:
                raise exceptions.FilterInvalid(arg)

    return filters, command, mods, description


def main():
    # Create or update database schema
    models.create_all()

    with db.get_session() as session:
        db.session = session

    first_arg = ""
    if len(sys.argv) > 1:
        first_arg = sys.argv[1]
    if "h" in first_arg:
        print("Python command line TODO manager with time tracking")
        exit(0)

    filters, command, mods, description = get_params()
    print(filters, command, mods, description)

    if command is None or "ls".startswith(command):
        cmd.tasks(filters)

    elif "add".startswith(command):
        params = {"description": description}
        if "project" in mods:
            params["project"] = mods["project"]
        if "urgency" in mods:
            params["urgency"] = mods["urgency"]
        cmd.add_task(**params)

    elif "mod".startswith(command):
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

    elif "done".startswith(command):
        if "pointers" in filters:
            for pointer_id in filters["pointers"]:
                task = cmd.get_task(pointer_id)
                cmd.complete_task(task.uuid)
        else:
            raise exceptions.FilterRequired("Id")

    elif "started".startswith(command):
        filters["mods"]["started"] = True
        cmd.tasks(filters)

    elif "begin".startswith(command):
        if "pointers" in filters:
            for pointer_id in filters["pointers"]:
                task = cmd.get_task(pointer_id)
                cmd.start_task(task.uuid)
        else:
            raise exceptions.FilterRequired("Id")

    elif "end".startswith(command):
        if "pointers" in filters:
            for pointer_id in filters["pointers"]:
                task = cmd.get_task(pointer_id)
                cmd.end_task(task.uuid)
        else:
            raise exceptions.FilterRequired("Id")

    else:
        # Listing tasks is the default action.

        # Being a bit lazy here, instead of making the regex parsing smarter
        # we assume the command forms part of the description filter.
        composite_description = ""
        if command is not None:
            composite_description += command
        if description is not None:
            composite_description += " " + description

        # Overwrite the description mod when using this form.
        filters["mods"]["description"] = composite_description

        cmd.tasks(filters)