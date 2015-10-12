# from sqlalchemy import Table
from sqlalchemy import Column, String, TIMESTAMP, ForeignKeyConstraint

from ..db import db

db_timestamp = TIMESTAMP(timezone="UTC")

# ..............................................................................
# Example of reflecting existing database table
# class Client(MyBase, db.Base):
#     __table__ = Table('client', db.metadata, autoload=True)


# ..............................................................................
class Entry(db.MyBase, db.Base):
    __tablename__ = 'entry'

    uuid = Column(String, primary_key=True)
    sheet = Column(String, index=True)
    start_time = Column(db_timestamp)
    end_time = Column(db_timestamp)
    modified = Column(db_timestamp)

    task_uuid = Column(String)
    ForeignKeyConstraint(["task"], ["Task.uuid"], name="fk_entry_task_uuid")


# ..............................................................................
class Task(db.MyBase, db.Base):
    __tablename__ = 'task'

    # Hash of uuid and description
    uuid = Column(String, primary_key=True)
    project = Column(String)
    description = Column(String)
    modified = Column(db_timestamp)


# ..............................................................................
def create_all():
    db.Base.metadata.create_all(db.engine)