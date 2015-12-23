import re
from taskmage.db import models
from taskmage.exceptions import exceptions
from collections import OrderedDict


def expand_command(arg):
    command_pattern = re.compile("^{}.*$".format(arg))
    matches = []

    for command in models.commands:
        match = command_pattern.match(command)
        if match is not None:
            matches.append(match.string)

    if len(matches) > 0:
        return matches

    return None


def expand_mod(arg):
    args = arg.split(":")
    key = args[0]
    value = args[1]
    key_pattern = re.compile("^{}.*$".format(key))
    value_pattern = re.compile("^{}.*$".format(value))

    found_key_match = None
    found_value_match = value
    for mod in models.mods:
        # Some mods have preset values,
        # if that is the case then the type will be list
        if type(mod) == str:
            # This mod does not have preset values
            mod = [mod]

        # Try to match the key
        key_match = key_pattern.match(mod[0])
        if key_match is not None:
            if found_key_match is None:
                found_key_match = key_match.string
            else:
                raise exceptions.ModAmbiguous

        # Only complete the value if this mod has preset values
        if found_key_match is not None and len(mod) > 1:
            for preset_value in mod[1]:
                value_match = value_pattern.match(preset_value)
                if value_match is not None:
                    found_value_match = value_match.string

    if found_key_match is not None:
        return [found_key_match, found_value_match]

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

    mod_pattern = re.compile('^\w+:[\w\W]+$')
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
                # Mod is an array of values
                if mod[0] in mods:
                    mods[mod[0]].append(mod[1])
                else:
                    mods[mod[0]] = [mod[1]]

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