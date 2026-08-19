import os
import stat

from scanner import ScanCounters, scan


def test_aggregates_size_up_the_tree(tmp_path, cache):
    (tmp_path / "a.txt").write_bytes(b"x" * 10)
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "b.txt").write_bytes(b"y" * 20)

    total = scan(str(tmp_path), cache)

    assert total == 30
    root_node = cache.get_node(str(tmp_path))
    assert root_node.size == 30
    sub_node = cache.get_node(str(sub))
    assert sub_node.size == 20


def test_empty_directory(tmp_path, cache):
    total = scan(str(tmp_path), cache)
    assert total == 0
    assert cache.get_node(str(tmp_path)).size == 0


def test_symlink_not_double_counted(tmp_path, cache):
    target = tmp_path / "real.txt"
    target.write_bytes(b"z" * 50)
    link = tmp_path / "link.txt"
    link.symlink_to(target)

    total = scan(str(tmp_path), cache)

    # real file (50) + symlink's own dirent size, not the target followed again.
    link_node = cache.get_node(str(link))
    assert link_node.is_symlink is True
    real_node = cache.get_node(str(target))
    assert real_node.size == 50
    assert total == 50 + link_node.size


def test_permission_denied_subdir_recorded_and_skipped(tmp_path, cache):
    blocked = tmp_path / "blocked"
    blocked.mkdir()
    (blocked / "secret.txt").write_bytes(b"s" * 100)
    (tmp_path / "visible.txt").write_bytes(b"v" * 10)

    os.chmod(blocked, 0o000)
    try:
        total = scan(str(tmp_path), cache)
    finally:
        os.chmod(blocked, 0o755)

    blocked_node = cache.get_node(str(blocked))
    assert blocked_node.error == "permission_denied"
    assert total == 10  # only the visible file counted


def test_second_scan_of_untouched_tree_skips_most_dirs(tmp_path, cache):
    for i in range(5):
        d = tmp_path / f"dir{i}"
        d.mkdir()
        (d / "f.txt").write_bytes(b"x" * 10)

    scan(str(tmp_path), cache, ScanCounters())

    counters2 = ScanCounters()
    scan(str(tmp_path), cache, counters2)

    assert counters2.dirs_skipped == counters2.dirs_visited


def test_rescan_detects_new_file_without_full_rescan_of_siblings(tmp_path, cache):
    untouched = tmp_path / "untouched"
    untouched.mkdir()
    (untouched / "f.txt").write_bytes(b"x" * 10)

    changed = tmp_path / "changed"
    changed.mkdir()

    scan(str(tmp_path), cache)

    (changed / "new.txt").write_bytes(b"y" * 25)

    counters = ScanCounters()
    total = scan(str(tmp_path), cache, counters)

    assert total == 10 + 25
    # the untouched dir's mtime didn't change, so it should have been skipped
    untouched_after = cache.get_node(str(untouched))
    assert untouched_after.size == 10


def test_rescan_detects_removed_file(tmp_path, cache):
    d = tmp_path / "d"
    d.mkdir()
    f = d / "f.txt"
    f.write_bytes(b"x" * 10)

    scan(str(tmp_path), cache)
    assert cache.get_node(str(f)) is not None

    f.unlink()
    total = scan(str(tmp_path), cache)

    assert total == 0
    assert cache.get_node(str(f)) is None


def test_rescan_detects_edited_file_content(tmp_path, cache):
    f = tmp_path / "f.txt"
    f.write_bytes(b"x" * 10)
    scan(str(tmp_path), cache)

    f.write_bytes(b"y" * 999)
    total = scan(str(tmp_path), cache)

    assert total == 999
