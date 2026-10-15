import os
import tempfile
from datetime import timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Point at a throwaway SQLite file before anything imports app.db, so tests
# never touch the Postgres the app runs against.
_tmp = tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False)
_tmp.close()
os.environ["DATABASE_URL"] = f"sqlite+pysqlite:///{_tmp.name}"

from app.db import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.service import now_local  # noqa: E402

engine = create_engine(os.environ["DATABASE_URL"], connect_args={"check_same_thread": False})
TestSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def _override_db():
    db = TestSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = _override_db


@pytest.fixture()
def client():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def machine(client):
    r = client.post("/api/machines", json={"label": "W1", "location": "Block A ground floor"})
    assert r.status_code == 201
    return r.json()


@pytest.fixture()
def tomorrow_10am():
    """A slot safely in the future, so the past-slot guard never fires."""
    base = now_local() + timedelta(days=1)
    return base.replace(hour=10, minute=0).isoformat()
