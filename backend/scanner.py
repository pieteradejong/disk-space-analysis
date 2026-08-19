"""Incremental filesystem scanner.

Governing fact this leans on: a directory's own mtime changes only when a
direct child is added/removed/renamed inside it. It does NOT change when a
file deeper in the subtree is edited, and it never propagates to ancestors.
So it's safe to skip re-listing (scandir) a directory whose mtime hasn't
changed since the last scan -- but it is never safe to skip *recursing* into
subdirectories on that basis, since a change could be nested arbitrarily
deep without touching this directory's own mtime. The walker therefore
always visits every directory node; what's skipped is only the enumeration
step for directories that are provably unchanged.

Known false negative (accepted, not solved): a file rewritten in place with
identical size and mtime looks unchanged to this scanner.
"""

from __future__ import annotations

import os
import stat as stat_module
from dataclasses import dataclass
from typing import Callable

from cache import Cache

ProgressCallback = Callable[["ScanCounters"], None]


@dataclass
class ScanCounters:
    dirs_visited: int = 0
    dirs_skipped: int = 0
    files_stated: int = 0


def scan(
    root_path: str,
    cache: Cache,
    counters: ScanCounters | None = None,
    on_progress: ProgressCallback | None = None,
) -> int:
    """Walk root_path, updating `cache` incrementally. Returns root_path's total size."""
    counters = counters if counters is not None else ScanCounters()
    root_path = os.path.abspath(root_path)
    _walk(root_path, None, root_path, cache, counters, on_progress)
    return cache.get_node(root_path).size


def _walk(
    dir_path: str,
    parent_path: str | None,
    scan_root: str,
    cache: Cache,
    counters: ScanCounters,
    on_progress: ProgressCallback | None,
) -> int:
    try:
        dir_stat = os.stat(dir_path, follow_symlinks=False)
    except (PermissionError, FileNotFoundError, OSError) as e:
        cache.upsert_node(
            path=dir_path, parent_path=parent_path, name=os.path.basename(dir_path) or dir_path,
            is_dir=True, size=0, error=_classify(e), scan_root=scan_root,
        )
        return 0

    cached = cache.get_node(dir_path)
    counters.dirs_visited += 1
    if on_progress is not None and counters.dirs_visited % 100 == 0:
        on_progress(counters)

    reuse_listing = (
        cached is not None
        and cached.is_dir
        and cached.error is None
        and cached.mtime == dir_stat.st_mtime
    )

    if reuse_listing:
        counters.dirs_skipped += 1
        entries = [(c.name, c.path) for c in cache.get_children(dir_path)]
    else:
        try:
            with os.scandir(dir_path) as it:
                entries = [(e.name, e.path) for e in it]
        except (PermissionError, OSError) as e:
            cache.upsert_node(
                path=dir_path, parent_path=parent_path, name=os.path.basename(dir_path) or dir_path,
                is_dir=True, size=0, error=_classify(e), scan_root=scan_root,
            )
            return 0
        child_names = {name for name, _ in entries}
        cache.reconcile_children(dir_path, child_names)

    total_size = 0
    for name, child_path in entries:
        try:
            lst = os.lstat(child_path)
        except (PermissionError, FileNotFoundError, OSError) as e:
            cache.upsert_node(
                path=child_path, parent_path=dir_path, name=name,
                is_dir=False, size=0, error=_classify(e), scan_root=scan_root,
            )
            continue

        if stat_module.S_ISLNK(lst.st_mode):
            cache.upsert_node(
                path=child_path, parent_path=dir_path, name=name,
                is_dir=False, is_symlink=True, size=lst.st_size, mtime=lst.st_mtime,
                scan_root=scan_root,
            )
            total_size += lst.st_size
        elif stat_module.S_ISDIR(lst.st_mode):
            total_size += _walk(child_path, dir_path, scan_root, cache, counters, on_progress)
        else:
            counters.files_stated += 1
            cached_file = cache.get_node(child_path)
            if cached_file is None or cached_file.mtime != lst.st_mtime or cached_file.size != lst.st_size:
                cache.upsert_node(
                    path=child_path, parent_path=dir_path, name=name,
                    is_dir=False, size=lst.st_size, mtime=lst.st_mtime, scan_root=scan_root,
                )
            total_size += lst.st_size

    cache.upsert_node(
        path=dir_path, parent_path=parent_path, name=os.path.basename(dir_path) or dir_path,
        is_dir=True, size=total_size, mtime=dir_stat.st_mtime, scan_root=scan_root,
    )
    return total_size


def _classify(e: OSError) -> str:
    if isinstance(e, PermissionError):
        return "permission_denied"
    if isinstance(e, FileNotFoundError):
        return "not_found"
    return "error"
