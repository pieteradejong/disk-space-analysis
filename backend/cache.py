"""SQLite-backed cache of scanned filesystem nodes.

A `Cache` instance owns one sqlite3 connection for its lifetime. The scanner
opens one Cache per scan (so a long walk isn't paying per-statement connection
overhead); API request handlers open a short-lived Cache per request.
"""

from __future__ import annotations

import sqlite3
import time
from dataclasses import dataclass

SCHEMA = """
CREATE TABLE IF NOT EXISTS nodes (
    path         TEXT PRIMARY KEY,
    parent_path  TEXT,
    name         TEXT NOT NULL,
    is_dir       INTEGER NOT NULL,
    is_symlink   INTEGER NOT NULL DEFAULT 0,
    size         INTEGER NOT NULL DEFAULT 0,
    mtime        REAL,
    last_scanned REAL NOT NULL,
    error        TEXT,
    scan_root    TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_nodes_parent ON nodes(parent_path);
CREATE INDEX IF NOT EXISTS idx_nodes_scan_root ON nodes(scan_root);

CREATE TABLE IF NOT EXISTS scans (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    root_path     TEXT NOT NULL,
    status        TEXT NOT NULL,
    started_at    REAL NOT NULL,
    finished_at   REAL,
    dirs_visited  INTEGER NOT NULL DEFAULT 0,
    dirs_skipped  INTEGER NOT NULL DEFAULT 0,
    files_stated  INTEGER NOT NULL DEFAULT 0,
    error_message TEXT
);
"""


@dataclass
class Node:
    path: str
    parent_path: str | None
    name: str
    is_dir: bool
    is_symlink: bool
    size: int
    mtime: float | None
    last_scanned: float
    error: str | None
    scan_root: str


@dataclass
class Scan:
    id: int
    root_path: str
    status: str
    started_at: float
    finished_at: float | None
    dirs_visited: int
    dirs_skipped: int
    files_stated: int
    error_message: str | None


class Cache:
    def __init__(self, db_path: str):
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()

    def __enter__(self) -> "Cache":
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    def commit(self) -> None:
        self.conn.commit()

    # --- nodes ---

    def upsert_node(
        self,
        *,
        path: str,
        parent_path: str | None,
        name: str,
        is_dir: bool,
        scan_root: str,
        is_symlink: bool = False,
        size: int = 0,
        mtime: float | None = None,
        last_scanned: float | None = None,
        error: str | None = None,
    ) -> None:
        last_scanned = last_scanned if last_scanned is not None else time.time()
        self.conn.execute(
            """
            INSERT INTO nodes
                (path, parent_path, name, is_dir, is_symlink, size, mtime, last_scanned, error, scan_root)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(path) DO UPDATE SET
                parent_path=excluded.parent_path,
                name=excluded.name,
                is_dir=excluded.is_dir,
                is_symlink=excluded.is_symlink,
                size=excluded.size,
                mtime=excluded.mtime,
                last_scanned=excluded.last_scanned,
                error=excluded.error,
                scan_root=excluded.scan_root
            """,
            (
                path,
                parent_path,
                name,
                int(is_dir),
                int(is_symlink),
                size,
                mtime,
                last_scanned,
                error,
                scan_root,
            ),
        )

    def get_node(self, path: str) -> Node | None:
        row = self.conn.execute("SELECT * FROM nodes WHERE path = ?", (path,)).fetchone()
        return _row_to_node(row) if row else None

    def get_children(self, parent_path: str) -> list[Node]:
        rows = self.conn.execute(
            "SELECT * FROM nodes WHERE parent_path = ? ORDER BY name", (parent_path,)
        ).fetchall()
        return [_row_to_node(r) for r in rows]

    def delete_subtree(self, path: str) -> None:
        """Delete `path` and every descendant reachable through parent_path links."""
        to_delete = [path]
        i = 0
        while i < len(to_delete):
            rows = self.conn.execute(
                "SELECT path FROM nodes WHERE parent_path = ?", (to_delete[i],)
            ).fetchall()
            to_delete.extend(row["path"] for row in rows)
            i += 1
        self.conn.executemany("DELETE FROM nodes WHERE path = ?", [(p,) for p in to_delete])

    def reconcile_children(self, parent_path: str, current_names: set[str]) -> None:
        """Drop cached children (and their subtrees) that no longer exist on disk."""
        for child in self.get_children(parent_path):
            if child.name not in current_names:
                self.delete_subtree(child.path)

    # --- scans ---

    def create_scan(self, root_path: str) -> int:
        cur = self.conn.execute(
            "INSERT INTO scans (root_path, status, started_at) VALUES (?, 'running', ?)",
            (root_path, time.time()),
        )
        self.conn.commit()
        return cur.lastrowid

    def get_running_scan(self, root_path: str) -> Scan | None:
        row = self.conn.execute(
            "SELECT * FROM scans WHERE root_path = ? AND status = 'running' ORDER BY id DESC LIMIT 1",
            (root_path,),
        ).fetchone()
        return _row_to_scan(row) if row else None

    def get_scan(self, scan_id: int) -> Scan | None:
        row = self.conn.execute("SELECT * FROM scans WHERE id = ?", (scan_id,)).fetchone()
        return _row_to_scan(row) if row else None

    def update_scan(self, scan_id: int, **fields) -> None:
        if not fields:
            return
        set_clause = ", ".join(f"{k} = ?" for k in fields)
        self.conn.execute(
            f"UPDATE scans SET {set_clause} WHERE id = ?", (*fields.values(), scan_id)
        )
        self.conn.commit()

    def get_largest(self, root_path: str, is_dir: bool, limit: int) -> list[Node]:
        """Top `limit` nodes of the given kind under `root_path` (any depth), by size.

        Uses a recursive CTE over parent_path rather than a path-prefix LIKE
        query, since the cache doesn't otherwise expose full subtree
        membership and LIKE would need escaping for paths containing % or _.
        """
        rows = self.conn.execute(
            """
            WITH RECURSIVE subtree(path) AS (
                SELECT path FROM nodes WHERE path = ?
                UNION ALL
                SELECT n.path FROM nodes n JOIN subtree s ON n.parent_path = s.path
            )
            SELECT n.* FROM nodes n
            JOIN subtree s ON n.path = s.path
            WHERE n.path != ? AND n.is_dir = ? AND n.error IS NULL
            ORDER BY n.size DESC
            LIMIT ?
            """,
            (root_path, root_path, int(is_dir), limit),
        ).fetchall()
        return [_row_to_node(r) for r in rows]

    def list_roots(self) -> list[dict]:
        """Latest scan per root_path, with its cached aggregate size."""
        rows = self.conn.execute(
            """
            SELECT s.root_path AS root_path,
                   s.status AS status,
                   s.finished_at AS last_scanned,
                   (SELECT size FROM nodes n WHERE n.path = s.root_path) AS total_size
            FROM scans s
            JOIN (
                SELECT root_path, MAX(id) AS max_id FROM scans GROUP BY root_path
            ) latest ON s.root_path = latest.root_path AND s.id = latest.max_id
            ORDER BY s.started_at DESC
            """
        ).fetchall()
        return [dict(r) for r in rows]


def _row_to_node(row: sqlite3.Row) -> Node:
    return Node(
        path=row["path"],
        parent_path=row["parent_path"],
        name=row["name"],
        is_dir=bool(row["is_dir"]),
        is_symlink=bool(row["is_symlink"]),
        size=row["size"],
        mtime=row["mtime"],
        last_scanned=row["last_scanned"],
        error=row["error"],
        scan_root=row["scan_root"],
    )


def _row_to_scan(row: sqlite3.Row) -> Scan:
    return Scan(
        id=row["id"],
        root_path=row["root_path"],
        status=row["status"],
        started_at=row["started_at"],
        finished_at=row["finished_at"],
        dirs_visited=row["dirs_visited"],
        dirs_skipped=row["dirs_skipped"],
        files_stated=row["files_stated"],
        error_message=row["error_message"],
    )
