import os

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session


TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "").strip()

if not TEST_DATABASE_URL:
    pytest.skip("TEST_DATABASE_URL is required for PostgreSQL integration tests.", allow_module_level=True)

url = make_url(TEST_DATABASE_URL)
if url.get_backend_name() == "sqlite":
    raise RuntimeError("SQLite is not allowed for integration tests. Use PostgreSQL via TEST_DATABASE_URL.")

if url.drivername in {"postgres", "postgresql"}:
    url = url.set(drivername="postgresql+psycopg")

os.environ["DATABASE_URL"] = url.render_as_string(hide_password=False)

ENGINE = create_engine(os.environ["DATABASE_URL"], pool_pre_ping=True, pool_recycle=300)


@pytest.fixture(scope="session")
def postgres_engine():
    return ENGINE


@pytest.fixture
def db(postgres_engine):
    connection = postgres_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    nested = connection.begin_nested()

    @event.listens_for(session, "after_transaction_end")
    def restart_savepoint(sess, trans):
        nonlocal nested
        if trans.nested and not trans._parent.nested:
            nested = connection.begin_nested()

    try:
        yield session
    finally:
        event.remove(session, "after_transaction_end", restart_savepoint)
        session.close()
        if nested.is_active:
            nested.rollback()
        if transaction.is_active:
            transaction.rollback()
        connection.close()
