# http://stackoverflow.com/questions/6290162/how-to-automatically-reflect-database-to-sqlalchemy-declarative
from sqlalchemy import event, create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker
from contextlib import contextmanager
from collections import OrderedDict
import uuid
import json
import datetime

from ..config import config

db_config = config["db"]

# ..............................................................................
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
                    # this will fail on non encode-able values, like other classes
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
    def _all_subclasses(my_class):
        """ Get all subclasses of my_class, descending.
        So, if A is a subclass of B is a subclass of my_class,
        this will include A and B. (Does not include my_class) """
        children = my_class.__subclasses__()
        result = []
        while children:
          next = children.pop()
          subclasses = next.__subclasses__()
          result.append(next)
          for subclass in subclasses:
            children.append(subclass)
        return result

# Create listener
def update_created_modified_on_create_listener(mapper, connection, target):
    if target.uuid is None:
        # For all tables except task we want to generate UUIDs
        uuid.uuid1()
    target.modified = datetime.utcnow()

# Update listener
def update_modified_on_update_listener(mapper, connection, target):
    target.modified = datetime.utcnow()

for my_class in MyBase._all_subclasses():
    event.listen(my_class, 'before_insert',  update_created_modified_on_create_listener)
    event.listen(my_class, 'before_update',  update_modified_on_update_listener)


# ..............................................................................
Base = declarative_base()

# Create an engine and get the metadata
engine = create_engine(
    "sqlite:///%s" % (
        db_config["path"],
    ),
    # Write out all sql statements
    echo=True,
)
metadata = MetaData(bind=engine)

session_factory = sessionmaker(bind=engine)

# Don't use ScopedSession in the main script!
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


# We have to use a ScopedSession with SQLAlchemy when using threads
# http://stackoverflow.com/questions/6297404/multi-threaded-use-of-sqlalchemy
# http://docs.sqlalchemy.org/en/rel_0_7/orm/session.html#contextual-thread-local-sessions
ScopedSession = scoped_session(session_factory)

@contextmanager
def get_scoped_session():
    try:
        db_session = ScopedSession()
        yield db_session
    except Exception as e:
        raise e
    else:
        # This gets executed if there was no exception
        pass
    finally:
        # This gets executed after the with statement completes.
        # Remove scoped session for the current thread.
        # http://docs.sqlalchemy.org/en/improve_toc/orm/contextual.html#using-thread-local-scope-with-web-applications
        ScopedSession.remove()



