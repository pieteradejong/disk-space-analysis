def test_upsert_and_get_node(cache):
    cache.upsert_node(
        path="/root/a", parent_path="/root", name="a",
        is_dir=False, size=100, mtime=1.0, scan_root="/root",
    )
    node = cache.get_node("/root/a")
    assert node.size == 100
    assert node.mtime == 1.0
    assert node.is_dir is False


def test_upsert_is_idempotent_update(cache):
    cache.upsert_node(
        path="/root/a", parent_path="/root", name="a",
        is_dir=False, size=100, mtime=1.0, scan_root="/root",
    )
    cache.upsert_node(
        path="/root/a", parent_path="/root", name="a",
        is_dir=False, size=200, mtime=2.0, scan_root="/root",
    )
    node = cache.get_node("/root/a")
    assert node.size == 200
    assert node.mtime == 2.0


def test_get_node_missing_returns_none(cache):
    assert cache.get_node("/nope") is None


def test_get_children_ordered_by_name(cache):
    for name in ["c", "a", "b"]:
        cache.upsert_node(
            path=f"/root/{name}", parent_path="/root", name=name,
            is_dir=False, size=1, mtime=1.0, scan_root="/root",
        )
    children = cache.get_children("/root")
    assert [c.name for c in children] == ["a", "b", "c"]


def test_delete_subtree_removes_descendants(cache):
    cache.upsert_node(path="/root", parent_path=None, name="root", is_dir=True, scan_root="/root")
    cache.upsert_node(path="/root/sub", parent_path="/root", name="sub", is_dir=True, scan_root="/root")
    cache.upsert_node(path="/root/sub/file", parent_path="/root/sub", name="file", is_dir=False, size=5, scan_root="/root")

    cache.delete_subtree("/root/sub")

    assert cache.get_node("/root/sub") is None
    assert cache.get_node("/root/sub/file") is None
    assert cache.get_node("/root") is not None


def test_reconcile_children_drops_removed_entries(cache):
    cache.upsert_node(path="/root", parent_path=None, name="root", is_dir=True, scan_root="/root")
    cache.upsert_node(path="/root/keep", parent_path="/root", name="keep", is_dir=False, size=1, scan_root="/root")
    cache.upsert_node(path="/root/gone", parent_path="/root", name="gone", is_dir=False, size=1, scan_root="/root")
    cache.upsert_node(path="/root/gone_dir", parent_path="/root", name="gone_dir", is_dir=True, scan_root="/root")
    cache.upsert_node(path="/root/gone_dir/child", parent_path="/root/gone_dir", name="child", is_dir=False, size=1, scan_root="/root")

    cache.reconcile_children("/root", current_names={"keep"})

    remaining = {c.name for c in cache.get_children("/root")}
    assert remaining == {"keep"}
    assert cache.get_node("/root/gone_dir/child") is None


def test_scan_lifecycle(cache):
    scan_id = cache.create_scan("/root")
    scan = cache.get_scan(scan_id)
    assert scan.status == "running"
    assert scan.root_path == "/root"

    cache.update_scan(scan_id, dirs_visited=10, dirs_skipped=3, files_stated=50)
    scan = cache.get_scan(scan_id)
    assert scan.dirs_visited == 10
    assert scan.dirs_skipped == 3

    cache.update_scan(scan_id, status="done", finished_at=123.0)
    scan = cache.get_scan(scan_id)
    assert scan.status == "done"
    assert scan.finished_at == 123.0


def test_get_running_scan(cache):
    assert cache.get_running_scan("/root") is None
    scan_id = cache.create_scan("/root")
    running = cache.get_running_scan("/root")
    assert running.id == scan_id

    cache.update_scan(scan_id, status="done", finished_at=1.0)
    assert cache.get_running_scan("/root") is None


def test_get_largest_files_ranks_by_size_across_full_depth(cache):
    cache.upsert_node(path="/root", parent_path=None, name="root", is_dir=True, scan_root="/root")
    cache.upsert_node(path="/root/small.txt", parent_path="/root", name="small.txt", is_dir=False, size=10, scan_root="/root")
    cache.upsert_node(path="/root/deep", parent_path="/root", name="deep", is_dir=True, scan_root="/root")
    cache.upsert_node(path="/root/deep/deeper", parent_path="/root/deep", name="deeper", is_dir=True, scan_root="/root")
    cache.upsert_node(
        path="/root/deep/deeper/big.bin", parent_path="/root/deep/deeper", name="big.bin",
        is_dir=False, size=1000, scan_root="/root",
    )

    largest = cache.get_largest("/root", is_dir=False, limit=10)

    assert [n.path for n in largest] == ["/root/deep/deeper/big.bin", "/root/small.txt"]


def test_get_largest_dirs_excludes_root_itself(cache):
    cache.upsert_node(path="/root", parent_path=None, name="root", is_dir=True, size=100, scan_root="/root")
    cache.upsert_node(path="/root/sub", parent_path="/root", name="sub", is_dir=True, size=60, scan_root="/root")

    largest = cache.get_largest("/root", is_dir=True, limit=10)

    assert [n.path for n in largest] == ["/root/sub"]


def test_get_largest_respects_limit(cache):
    cache.upsert_node(path="/root", parent_path=None, name="root", is_dir=True, scan_root="/root")
    for i in range(5):
        cache.upsert_node(
            path=f"/root/f{i}", parent_path="/root", name=f"f{i}",
            is_dir=False, size=i, scan_root="/root",
        )

    largest = cache.get_largest("/root", is_dir=False, limit=2)

    assert [n.path for n in largest] == ["/root/f4", "/root/f3"]


def test_list_roots_returns_latest_scan_per_root(cache):
    cache.upsert_node(path="/root", parent_path=None, name="root", is_dir=True, size=999, scan_root="/root")
    first = cache.create_scan("/root")
    cache.update_scan(first, status="done", finished_at=1.0)
    second = cache.create_scan("/root")
    cache.update_scan(second, status="done", finished_at=2.0)

    roots = cache.list_roots()
    assert len(roots) == 1
    assert roots[0]["root_path"] == "/root"
    assert roots[0]["last_scanned"] == 2.0
    assert roots[0]["total_size"] == 999
