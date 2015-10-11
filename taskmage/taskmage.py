# -*- coding: utf-8 -*-


"""taskmage.taskmage: provides entry point main()."""


__version__ = "0.0.1"


import sys
from taskmage.db import db, models

def main():
    print("Executing bootstrap version %s." % __version__)
    print("List of argument strings: %s" % sys.argv[1:])

    with db.get_session() as session:
        db.Base.metadata.create_all(db.engine)

        # task = models.Task()
        # task.hash = "1"
        # task.uuid = "bebf9c9e-fc83-46a0-bf18-f397cb4e9675"
        # task.description = "Replication with Differing Table Definitions on Master and Slave"
        # print(task)
        #
        # session.add(task)
        # session.commit()

        tasks = session.query(models.Task).all()
        for task in tasks:
            print(task)