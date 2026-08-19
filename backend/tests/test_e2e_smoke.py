"""Contract test: real scan -> real API -> shape the frontend expects.

Mirrors frontend/src/lib/types.ts. If this drifts from that file, the
frontend will break at runtime even though this test and the TS build both
pass -- there's no automated cross-language check, so keep them in sync by
hand when either side's response/type shape changes.
"""

import time


def test_scan_to_tree_response_matches_frontend_contract(tmp_path, client):
    (tmp_path / "a.txt").write_bytes(b"x" * 7)
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "b.txt").write_bytes(b"y" * 3)

    scan_resp = client.post("/api/scan", json={"root_path": str(tmp_path)})
    assert scan_resp.status_code == 200
    scan_body = scan_resp.json()
    assert set(scan_body) == {"scan_id", "root_path", "status"}

    scan_id = scan_body["scan_id"]
    deadline = time.time() + 5
    status_body = None
    while time.time() < deadline:
        status_resp = client.get(f"/api/scan/{scan_id}/status")
        assert status_resp.status_code == 200
        status_body = status_resp.json()
        if status_body["status"] in ("done", "error"):
            break
        time.sleep(0.05)

    assert status_body is not None
    assert status_body["status"] == "done"
    assert set(status_body) == {
        "scan_id", "root_path", "status", "dirs_visited", "dirs_skipped",
        "files_stated", "elapsed_seconds", "error_message",
    }

    tree_resp = client.get("/api/tree", params={"root_path": str(tmp_path)})
    assert tree_resp.status_code == 200
    tree_body = tree_resp.json()
    assert set(tree_body) == {
        "path", "name", "size", "is_dir", "mtime", "last_scanned", "error", "children",
    }
    assert tree_body["size"] == 10
    assert tree_body["is_dir"] is True
    assert len(tree_body["children"]) == 2
    for child in tree_body["children"]:
        assert set(child) == {
            "path", "name", "size", "is_dir", "mtime", "last_scanned", "error", "children",
        }

    roots_resp = client.get("/api/roots")
    assert roots_resp.status_code == 200
    roots_body = roots_resp.json()
    assert len(roots_body) == 1
    assert set(roots_body[0]) == {"root_path", "last_scanned", "total_size", "status"}
