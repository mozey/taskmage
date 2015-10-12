#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import os, sys
from taskmage.db import db

class Tests(unittest.TestCase):
    def setUp(self):
        print("") # Make taskmage output go onto newline
        db.Base.metadata.create_all(db.engine)

    def test_start_entry(self):
        from taskmage.cmd import add_entry
        add_entry(
            uuid="11111111-1111-1111-1111-111111111111",
            project="indigo",
            description="This is the first task"
        )

    def test_stop_entry(self):
        from taskmage.cmd import add_entry
        add_entry(
            uuid="11111111-1111-1111-1111-111111111111",
            project="indigo",
            description="This is the first task"
        )

    def test_adjust_entry(self):
        pass


if __name__ == "__main__":
    verbose = False
    for arg in sys.argv:
        if arg == "-v" or arg == "--verbose":
            verbose = True

    # Hijack verbose param from unittest
    if not verbose:
        f = open(os.devnull, 'w')
        sys.stdout = f

    unittest.main()
