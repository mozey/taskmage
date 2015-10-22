#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import os, sys
from taskmage import config

config.testing = True
# config.echo = True
# config.echo = False

from taskmage.db import db, models
from taskmage import cmd

class Tests(unittest.TestCase):
    def setUp(self):
        # Each test starts with an empty database
        db.Base.metadata.drop_all(db.engine)
        models.create_all()

        with db.get_session() as session:
            db.session = session


    def test_add_task(self):
        task_in = {
            "uuid": "11111111-1111-1111-1111-111111111111",
            "project": "indigo",
            "description": "This is the first task",
            "priority": "H",
        }
        cmd.touch_task(**task_in)

        task_from_uuid = cmd.get_task(task_in["uuid"])
        self.assertIsNotNone(task_from_uuid)

        task_from_id = cmd.get_task(1)
        self.assertIsNotNone(task_from_id)

        for key in task_in:
            self.assertEqual(task_in[key], task_from_uuid.__getattribute__(key))
            self.assertEqual(task_in[key], task_from_id.__getattribute__(key))


    def test_update_task(self):
        self.test_add_task()

        task_in = {
            "uuid": "11111111-1111-1111-1111-111111111111",
            "project": "magento",
            "description": "This is the first task updated",
            "priority": "L",
        }
        cmd.touch_task(**task_in)

        task_out = cmd.get_task(task_in["uuid"])
        for key in task_in:
            self.assertEqual(task_in[key], task_out.__getattribute__(key))


    def test_start_task(self):
        self.test_add_task()

        task_uuid = "11111111-1111-1111-1111-111111111111";
        cmd.start_task(task_uuid)
        entry = db.session.query(models.entry).filter_by(task_uuid=task_uuid).first()
        print(entry)
        # for key in entry.__getattributes__():
        #     self.assertIsNotNone(entry.)


    def test_complete_task(self):
        self.test_start_task()


    def test_stop_task(self):
        cmd.stop_task("11111111-1111-1111-1111-111111111111")


    def test_list_tasks(self):
        self.test_add_task()

        cmd.tasks()


if __name__ == "__main__":
    verbose = False
    for arg in sys.argv:
        if arg == "-v" or arg == "--verbose":
            verbose = True

    # Hijack verbose param from unittest
    if not verbose:
        # Redirect stdout to devnull
        f = open(os.devnull, 'w')
        sys.stdout = f

    unittest.main()
