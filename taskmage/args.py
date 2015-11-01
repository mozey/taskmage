import re
from taskmage.db import models
from taskmage.exceptions import exceptions
from collections import OrderedDict

def expand_command(arg):
    pattern = re.compile("^{}.*$".format(arg))
    pattern_match = pattern.match

    found_match = None
    for command in models.commands:
        match = pattern_match(command)
        if match is not None:
            if found_match is None:
                found_match = match
            else:
                raise exceptions.CommandAmbiguous

    if found_match is not None:
        return found_match.string

    return None


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

    raise exceptions.ModNotFound


def pointer_required(filters):
    if len(filters["pointers"]) == 0:
        raise exceptions.FilterRequired("Id")


def parse(argv):
    '''
    Command must consist of word characters only
    Filters => 1 or 1,2 or +tag or attr:value
    Mods => key:value
    '''

    filters = OrderedDict()
    filters["mods"] = OrderedDict()
    filters["pointers"] = []

    command = None
    mods = OrderedDict()
    description = None

    mod_pattern = re.compile('^\w+:\w+$')
    pointer_pattern = re.compile('^\d+$')
    # TODO range must support 1,2,3 or 1-3
    # range_pattern = re.compile('^(\d+,\d+)$')

    for arg in argv[1:]:

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

    command = expand_command(command)

    return filters, command, mods, description