import pytest
from fastapi.testclient import TestClient

import main
from cache import Cache


@pytest.fixture
def cache(tmp_path_factory) -> Cache:
    # Deliberately outside the `tmp_path` scan-target fixture used by scanner
    # tests -- the cache DB (plus its -wal/-shm files) must not live inside a
    # directory that's also being scanned, or it inflates the counted size.
    db_dir = tmp_path_factory.mktemp("cache")
    with Cache(str(db_dir / "cache.db")) as c:
        yield c


@pytest.fixture
def client(tmp_path_factory, monkeypatch) -> TestClient:
    db_dir = tmp_path_factory.mktemp("api_cache")
    monkeypatch.setattr(main, "DB_PATH", str(db_dir / "cache.db"))
    return TestClient(main.app)
