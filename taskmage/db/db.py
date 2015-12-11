# http://stackoverflow.com/questions/6290162/how-to-automatically-reflect-database-to-sqlalchemy-declarative
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
from collections import OrderedDict
import json
import os
import re
from taskmage import config
from datetime import datetime

# TODO Type annotations?
session = None

# The default database path is ~/.task/taskmage.db,
# override this by setting taskmage.data.location="path/to/taskmage.db"
# in ~/.taskrc
home_dir = os.path.expanduser('~')

db_name = "taskmage.db"
if config.testing:
    # It's annoying if the test database location is changing all the time.
    # db_path = os.path.join(tempfile.gettempdir(), db_name)
    # Rather used a fixed location
    db_name = "taskmage.testing.db"

app_path = os.path.join(home_dir, ".taskmage")
db_path = os.path.join(app_path, db_name)

# Try to override default database location
try:
    db_path_override = re.search(
        'taskmage\.data\.location=(.*)',
        open(os.path.join(home_dir, ".taskmagerc")).read(),
    )
    if db_path_override:
        db_path = os.path.join(db_path_override.group(1), db_name)
except FileNotFoundError as e:
    pass

if config.testing:
    print("sqlite3", db_path);

timestamp_format = "%Y-%m-%d %H:%M:%S"

# ..............................................................................
# Serialize SqlAlchemy result to JSON
# http://stackoverflow.com/a/10664192/639133
from sqlalchemy.ext.declarative import DeclarativeMeta


class AlchemyEncoder(json.JSONEncoder):
    def default(self, obj):
        fields = {}
        if isinstance(obj.__class__, DeclarativeMeta):
            # a SQLAlchemy class
            for field in [x for x in dir(obj) if
                          not x.startswith('_') and x != 'metadata']:
                data = obj.__getattribute__(field)
                try:
                    if isinstance(data, datetime):
                        data = datetime.strftime(data, timestamp_format)
                    else:
                        # this will fail on non encode-able values,
                        # like other classes
                        json.dumps(data)

                    fields[field] = data

                except TypeError:
                    fields[field] = None

        else:
            fields = json.JSONEncoder.default(self, obj)

        # Modified to always return data ordered by key
        return OrderedDict(sorted(fields.items()))


# ..............................................................................
class MyBase():
    # From event listeners post link below, doesn't work.
    # __abstract__ = True

    def __repr__(self):
        return json.dumps(self, cls=AlchemyEncoder)

    # Used for adding event listeners to all models
    # http://stackoverflow.com/a/13979333/639133
    @classmethod
    def _all_subclasses(self):
        """ Get all subclasses of my_class, descending.
        So, if A is a subclass of B is a subclass of my_class,
        this will include A and B. (Does not include my_class) """
        children = self.__subclasses__()
        result = []
        while children:
            next = children.pop()
            subclasses = next.__subclasses__()
            result.append(next)
            for subclass in subclasses:
                children.append(subclass)
        return result

# ..............................................................................
Base = declarative_base()

# Create an engine and get the metadata
engine = create_engine(
    "sqlite:///{}".format(db_path),
    # Write out all sql statements
    echo=config.echo,
)

# http://docs.sqlalchemy.org/en/rel_0_9/core/constraints.html
convention = {
    "ix": 'ix_%(column_0_label)s',
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

metadata = MetaData(bind=engine, naming_convention=convention)

session_factory = sessionmaker(bind=engine)

# ..............................................................................
# Use get_session when not using threads.
@contextmanager
def get_session():
    try:
        db_session = session_factory()
        yield db_session
    except Exception as e:
        raise e
    else:
        # This gets executed if there was no exception
        pass
    finally:
        db_session.close()
