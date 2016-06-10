#!/usr/bin/env python3
# -*- coding: utf-8 -*-


"""Convenience wrapper for running taskmage directly from source tree."""

from taskmage.exceptions import exceptions
from taskmage.taskmage import main
import sys

if __name__ == '__main__':
    try:
        main()

    except KeyboardInterrupt:
        # Exit on KeyboardInterrupt
        # http://stackoverflow.com/a/21144662/639133
        print()
        print('Keyboard interrupt')
        sys.exit(0)

    except Exception as e:
        # Check if this is a taskmage.exception
        # http://stackoverflow.com/a/7584517/639133
        taskmage_exceptions = dict(
            [(name, cls) for name, cls
            in exceptions.__dict__.items() if isinstance(cls, type)]
        )
        for name in taskmage_exceptions:
            if isinstance(e, taskmage_exceptions[name]):
                print(e.message)
                print()
                sys.exit(0)

        # Exception is not in taskmage.exceptions
        raise e
