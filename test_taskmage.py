#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import os, sys
from taskmage import config
from taskmage.exceptions import exceptions
import json
import datetime
from uuid import uuid4

config.testing = True
# config.echo = True
# config.echo = False

from taskmage.db import db, models
from taskmage import cmd
from taskmage import args

class Db(unittest.TestCase):
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


    def test_remove_task(self):
        self.test_add_task()
        self.test_complete_task()

        cmd.remove_task(self.task_uuid1, prompt=False)
        self.assertEqual(None, cmd.get_task(self.task_uuid1))

        entry = db.session.query(models.entry).filter_by(task_uuid=self.task_uuid1).first()
        self.assertEqual(None, entry)

        task_tag = db.session.query(models.task_tag).filter_by(task_uuid=self.task_uuid1).first()
        self.assertEqual(None, task_tag)


    def test_list_tasks(self):
        self.test_start_task()
        response = cmd.tasks({"mods": {"started": True}})
        self.assertEqual(len(response.data["rows"]), 1)


    def test_timesheet_report(self):
        sheet = "2015-11"
        project = "Project 1"

        task = models.task()
        task.uuid = self.task_uuid1
        task.description = "Completed task"
        task.project = project
        task.urgency = "m"
        task.completed = datetime.datetime.strptime("2015-11-03 09:21:00", db.timestamp_format)
        db.session.add(task)

        pointer = models.pointer()
        pointer.task_uuid = self.task_uuid1
        db.session.add(pointer)

        entry = models.entry()
        entry.uuid = uuid4().__str__()
        entry.start_time = datetime.datetime.strptime("2015-11-01 15:20:00", db.timestamp_format)
        entry.end_time = datetime.datetime.strptime("2015-11-01 17:05:00", db.timestamp_format)
        entry.task_uuid = self.task_uuid1
        entry.sheet = sheet
        db.session.add(entry)

        entry = models.entry()
        entry.uuid = uuid4().__str__()
        entry.start_time = datetime.datetime.strptime("2015-11-02 09:25:00", db.timestamp_format)
        entry.end_time = datetime.datetime.strptime("2015-11-02 12:00:00", db.timestamp_format)
        entry.task_uuid = self.task_uuid1
        entry.sheet = sheet
        db.session.add(entry)

        db.session.commit()

        filters={"mods": {
            "sheet": sheet,
            "project": project,
        }}
        response = cmd.timesheet_report(filters)

        self.assertEqual(response.data["rows"][0][4], "4:20")
        response.print()


    def test_list_entries(self):
        self.test_timesheet_report()
        task = cmd.get_task(1)
        response = cmd.list_entries(task.uuid)
        response.print()


class Args(unittest.TestCase):
    def test_expand_command(self):
        arg = "does_not_exist:something"
        self.assertEqual(None, args.expand_command(arg))

        # Starting all commands with a different letter will prevent ambiguity,
        # but we may run out of letters.
        commands = models.commands
        models.commands = ["ambiguous", "ambivalent"]
        arg = "a"
        self.assertRaises(exceptions.CommandAmbiguous, args.expand_command, arg)
        models.commands = commands

        command = models.commands[0]
        result = args.expand_command("{}".format(command[:1], command))
        self.assertEqual(result, command)


    def test_expand_mod(self):
        arg = "does_not_exist:something"
        self.assertRaises(exceptions.ModNotFound, args.expand_mod, arg)

        # Starting all mods with a different letter will prevent ambiguity,
        # but we may run out of letters.
        mods = models.mods
        models.mods = ["ambiguous", "ambivalent"]
        arg = "a:something"
        self.assertRaises(exceptions.ModAmbiguous, args.expand_mod, arg)
        models.mods = mods

        mod = models.mods[0]
        value = "something"
        expanded = [mod, value]
        result = args.expand_mod("{}:{}".format(mod[:1], value))
        self.assertEqual(result, expanded)


    def test_parse_add(self):
        argv = [None, "a", "p:something", "This is", "urg:m", "the description"];
        expected = '[{"mods": {}, "pointers": []}, "add", {"project": "something", "urgency": "m"}, "This is the description"]'
        result = json.dumps(args.parse(argv))
        self.assertEqual(expected, result)


    def test_parse_begin(self):
        argv = [None, "1", "beg"];
        expected = '[{"mods": {}, "pointers": ["1"]}, "begin", {}, null]'
        result = json.dumps(args.parse(argv))
        self.assertEqual(expected, result)


    def test_parse_list(self):
        argv = [None, "l", "foo"];
        expected = '[{"mods": {}, "pointers": []}, "ls", {}, "foo"]'
        result = json.dumps(args.parse(argv))
        self.assertEqual(expected, result)


    def test_parse_mod(self):
        argv = [None, "mo", "p:foo", "u:l"];
        expected = '[{"mods": {}, "pointers": []}, "mod", {"project": "foo", "urgency": "l"}, null]'
        result = json.dumps(args.parse(argv))
        self.assertEqual(expected, result)


    def test_parse_timesheet(self):
        argv = [None, "s:2015-11", "t"];
        expected = '[{"mods": {"sheet": "2015-11"}, "pointers": []}, "timesheet", {}, null]'
        result = json.dumps(args.parse(argv))
        self.assertEqual(expected, result)


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
