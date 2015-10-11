# from sqlalchemy import Table
from sqlalchemy import Column, Integer, String, TIMESTAMP, ForeignKeyConstraint
from sqlalchemy_utils import UUIDType
from collections import OrderedDict
import uuid
from ..db import db
import json

db_timestamp = TIMESTAMP(timezone="UTC")
db_uuid = UUIDType(binary=False)

# Serialize SqlAlchemy result to JSON
# http://stackoverflow.com/a/10664192/639133
from sqlalchemy.ext.declarative import DeclarativeMeta
class AlchemyEncoder(json.JSONEncoder):
    def default(self, obj):
        fields = {}
        if isinstance(obj.__class__, DeclarativeMeta):
            # a SQLAlchemy class
            for field in [x for x in dir(obj) if not x.startswith('_') and x != 'metadata']:
                data = obj.__getattribute__(field)
                try:
                    if isinstance(data, uuid.UUID):
                        fields[field] = data.__str__()

                    else:
                        # this will fail on non encode-able values, like other classes
                        json.dumps(data)
                        fields[field] = data

                except TypeError:
                    fields[field] = None

        else:
            fields = json.JSONEncoder.default(self, obj)

        # Modified to always return data ordered by key
        return OrderedDict(sorted(fields.items()))


class MyBase():
    def __repr__(self):
        return json.dumps(self, cls=AlchemyEncoder)


# Example of reflecting existing database table
# class Client(MyBase, db.Base):
#     __table__ = Table('client', db.metadata, autoload=True)


class Task(MyBase, db.Base):
    __tablename__ = 'task'

    # Hash of uuid and description
    hash = Column(String, primary_key=True)
    uuid = Column(db_uuid, index=True)
    description = Column(String)
    project = Column(String)


class Entry(MyBase, db.Base):
    __tablename__ = 'entry'

    uuid = Column(UUIDType, primary_key=True)
    sheet = Column(String, index=True)
    start_time = Column(db_timestamp)
    end_time = Column(db_timestamp)
    task = Column(String)
    ForeignKeyConstraint(["task"], ["Task.hash"])