# http://stackoverflow.com/questions/6290162/how-to-automatically-reflect-database-to-sqlalchemy-declarative
from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker
from contextlib import contextmanager

from ..config import config

db_config = config["db"]

# Create an engine and get the metadata
Base = declarative_base()
engine = create_engine(
    "sqlite:///%s" % (
        db_config["path"],
    ),
    # Write out all sql statements
    # echo=True,
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




