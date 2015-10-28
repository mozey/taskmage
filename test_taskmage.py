#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import os, sys
from taskmage import config
from taskmage.exceptions import exceptions

config.testing = True
# config.echo = True
# config.echo = False

from taskmage.db import db, models
from taskmage import cmd

class Tests(unittest.TestCase):
    def setUp(self):
        # Each test starts with an empty database.
        # TODO More efficient way to clear all tables and sync the schema before each test?
        db.Base.metadata.drop_all(db.engine)
        models.create_all()

        with db.get_session() as session:
            db.session = session

        self.task_uuid1 = "11111111-1111-1111-1111-111111111111"
        self.task_uuid2 = "22222222-2222-2222-2222-222222222222"


    def test_add_task(self):
        task_in = {
            "uuid": self.task_uuid1,
            "project": "indigo",
            "description": "This is the first task",
            "urgency": "h",
        }
        cmd.touch_task(**task_in)

        task_from_uuid = cmd.get_task(task_in["uuid"])
        self.assertIsNotNone(task_from_uuid)

        task_from_id = cmd.get_task(1)
        self.assertIsNotNone(task_from_id)

        for key in task_in:
            self.assertEqual(task_in[key], task_from_uuid.__getattribute__(key))
            self.assertEqual(task_in[key], task_from_id.__getattribute__(key))

        pointer = db.session.query(models.pointer).filter_by(task_uuid=self.task_uuid1).first()
        self.assertEqual(pointer.task_uuid, task_in["uuid"])


    def test_update_task(self):
        self.test_add_task()

        task_in = {
            "uuid": self.task_uuid1,
            "project": "violet",
            "description": "This is the updated task",
            "urgency": "l",
        }
        cmd.touch_task(**task_in)

        task_out = cmd.get_task(task_in["uuid"])
        for key in task_in:
            self.assertEqual(task_in[key], task_out.__getattribute__(key))


    def test_start_task(self):
        self.test_add_task()

        task_uuid = self.task_uuid1;
        cmd.start_task(task_uuid)
        entry = db.session.query(models.entry).filter_by(task_uuid=task_uuid).first()

        self.assertIsNone(entry.end_time)
        self.assertIsNotNone(entry.modified)
        self.assertEqual(entry.sheet, cmd.current_sheet())
        self.assertIsNotNone(entry.start_time)
        self.assertEqual(entry.task_uuid, task_uuid)
        self.assertIsNotNone(entry.uuid)


    def test_end_task(self):
        self.assertRaises(exceptions.TaskNotStarted, cmd.end_task, task_uuid=self.task_uuid2)

        self.test_start_task()
        cmd.end_task(self.task_uuid1)

        entry = db.session.query(models.entry).filter_by(task_uuid=self.task_uuid1).first()
        self.assertIsNotNone(entry.end_time)


    def test_complete_task(self):
        self.test_start_task()

        cmd.complete_task(self.task_uuid1)

        task = cmd.get_task(self.task_uuid1)
        self.assertIsNotNone(task.completed)

        entry = db.session.query(models.entry).filter_by(task_uuid=self.task_uuid1).first()
        self.assertIsNotNone(entry.end_time)

        pointer = db.session.query(models.pointer).filter_by(task_uuid=self.task_uuid1).first()
        self.assertIsNone(pointer)


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
