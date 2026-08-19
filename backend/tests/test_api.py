import time

import pytest

import main


@pytest.fixture
def scan_target(tmp_path):
    (tmp_path / "a.txt").write_bytes(b"x" * 42)
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "b.txt").write_bytes(b"y" * 8)
    return tmp_path


def _wait_for_done(client, scan_id, timeout=5):
    deadline = time.time() + timeout
    while time.time() < deadline:
        r = client.get(f"/api/scan/{scan_id}/status")
        assert r.status_code == 200
        body = r.json()
        if body["status"] in ("done", "error"):
            return body
        time.sleep(0.05)
    raise TimeoutError("scan did not finish in time")


def test_scan_nonexistent_path_returns_400(client):
    r = client.post("/api/scan", json={"root_path": "/definitely/not/a/real/path"})
    assert r.status_code == 400


def test_scan_then_status_then_tree(client, scan_target):
    r = client.post("/api/scan", json={"root_path": str(scan_target)})
    assert r.status_code == 200
    scan_id = r.json()["scan_id"]

    status = _wait_for_done(client, scan_id)
    assert status["status"] == "done"
    assert status["files_stated"] == 2

    tree = client.get("/api/tree", params={"root_path": str(scan_target)})
    assert tree.status_code == 200
    body = tree.json()
    assert body["size"] == 50
    assert body["is_dir"] is True
    names = {c["name"] for c in body["children"]}
    assert names == {"a.txt", "sub"}


def test_scan_already_running_returns_same_scan_id(client, scan_target, monkeypatch):
    from cache import Cache

    with Cache(main.DB_PATH) as cache:
        existing_id = cache.create_scan(str(scan_target.resolve()))

    r = client.post("/api/scan", json={"root_path": str(scan_target)})
    assert r.status_code == 200
    assert r.json()["scan_id"] == existing_id
    assert r.json()["status"] == "running"


def test_tree_without_prior_scan_returns_404(client, scan_target):
    r = client.get("/api/tree", params={"root_path": str(scan_target)})
    assert r.status_code == 404


def test_scan_status_unknown_id_returns_404(client):
    r = client.get("/api/scan/999999/status")
    assert r.status_code == 404


def test_largest_files_returns_deep_descendants_ranked_by_size(client, tmp_path):
    (tmp_path / "small.txt").write_bytes(b"x" * 10)
    nested = tmp_path / "a" / "b" / "c"
    nested.mkdir(parents=True)
    (nested / "big.bin").write_bytes(b"y" * 1000)

    scan_id = client.post("/api/scan", json={"root_path": str(tmp_path)}).json()["scan_id"]
    _wait_for_done(client, scan_id)

    r = client.get("/api/largest", params={"root_path": str(tmp_path), "kind": "files"})
    assert r.status_code == 200
    body = r.json()
    assert body[0]["name"] == "big.bin"
    assert body[0]["size"] == 1000
    assert all(not item["is_dir"] for item in body)


def test_largest_invalid_kind_returns_400(client, scan_target):
    r = client.get("/api/largest", params={"root_path": str(scan_target), "kind": "bogus"})
    assert r.status_code == 400


def test_largest_without_prior_scan_returns_404(client, scan_target):
    r = client.get("/api/largest", params={"root_path": str(scan_target)})
    assert r.status_code == 404


def test_roots_lists_scanned_roots_after_restart(client, scan_target):
    r = client.post("/api/scan", json={"root_path": str(scan_target)})
    scan_id = r.json()["scan_id"]
    _wait_for_done(client, scan_id)

    # simulate the app restarting: fresh Cache connection to the same DB file
    from cache import Cache

    with Cache(main.DB_PATH) as cache:
        roots = cache.list_roots()

    assert len(roots) == 1
    assert roots[0]["root_path"] == str(scan_target.resolve())
    assert roots[0]["status"] == "done"
    assert roots[0]["total_size"] == 50

    r2 = client.get("/api/roots")
    assert r2.status_code == 200
    body = r2.json()
    assert len(body) == 1
    assert body[0]["total_size"] == 50
