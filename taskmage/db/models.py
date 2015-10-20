# from sqlalchemy import Table
from sqlalchemy import Column, String, Integer, TIMESTAMP, event, ForeignKey
from sqlalchemy.orm import relationship, backref
import uuid
from datetime import datetime

from ..db import db

db_timestamp = TIMESTAMP(timezone="UTC")


# ..............................................................................
# Example of reflecting existing database table
# class Client(MyBase, db.Base):
#     __table__ = Table('client', db.metadata, autoload=True)


# ..............................................................................
class entry(db.MyBase, db.Base):
    __tablename__ = 'entry'

    uuid = Column(String, primary_key=True)
    sheet = Column(String, index=True)
    start_time = Column(db_timestamp)
    end_time = Column(db_timestamp)
    modified = Column(db_timestamp)

    task_uuid = Column(String, ForeignKey("task.uuid"), nullable=True, default=None)
    task = relationship("task", backref=backref("_entries", order_by=start_time))


# ..............................................................................
class task(db.MyBase, db.Base):
    __tablename__ = 'task'

    uuid = Column(String, primary_key=True)
    project = Column(String)
    priority = Column(String)
    description = Column(String)
    modified = Column(db_timestamp)
    completed = Column(db_timestamp)


# ..............................................................................
# The pointer table is used to assigned short IDs to pending tasks.
# Once a task is marked as completed it opens up a slot in the pointer table.
# If the pointer table is full when a new task is created we add a new row,
# otherwise an existing pointer row with null task_uuid is used.
class pointer(db.MyBase, db.Base):
    __tablename__ = 'pointer'
    # http://stackoverflow.com/a/4567698/639133
    __table_args__ = {"sqlite_autoincrement": True}

    id = Column(String, primary_key=True)

    task_uuid = Column(String, ForeignKey("task.uuid"), nullable=True, default=None)
    task = relationship("task", backref=backref("_pointer", order_by=id))


# ..............................................................................
class task_tag(db.MyBase, db.Base):
    __tablename__ = 'task_tag'

    # Hash of uuid and description
    uuid = Column(String, primary_key=True)
    modified = Column(db_timestamp)

    tag_uuid = Column(String, ForeignKey("tag.uuid"), nullable=True, default=None)
    tag = relationship("tag", backref=backref("_task_tags"))

    task_uuid = Column(String, ForeignKey("task.uuid"), nullable=True, default=None)
    task = relationship("task", backref=backref("_task_tags"))


# ..............................................................................
class tag(db.MyBase, db.Base):
    __tablename__ = 'tag'

    uuid = Column(String, primary_key=True)
    tag = Column(String)
    modified = Column(db_timestamp)


# ..............................................................................

# Create listener
def update_created_modified_on_create_listener(mapper, connection, target):
    if hasattr(target, "uuid") and target.uuid is None:
        # For all tables except task we want to generate UUIDs
        uuid.uuid4().__str__()
    target.modified = datetime.utcnow()

# Update listener
def update_modified_on_update_listener(mapper, connection, target):
    target.modified = datetime.utcnow()

for my_class in db.MyBase._all_subclasses():
    event.listen(my_class, 'before_insert',  update_created_modified_on_create_listener)
    event.listen(my_class, 'before_update',  update_modified_on_update_listener)


# ..............................................................................
def create_all():
    db.Base.metadata.create_all(db.engine)

