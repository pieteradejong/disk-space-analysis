from __future__ import annotations

from pydantic import BaseModel


class ScanRequest(BaseModel):
    root_path: str


class ScanResponse(BaseModel):
    scan_id: int
    root_path: str
    status: str


class ScanStatusResponse(BaseModel):
    scan_id: int
    root_path: str
    status: str
    dirs_visited: int
    dirs_skipped: int
    files_stated: int
    elapsed_seconds: float
    error_message: str | None = None


class TreeNode(BaseModel):
    path: str
    name: str
    size: int
    is_dir: bool
    mtime: float | None
    last_scanned: float
    error: str | None = None
    children: list["TreeNode"] = []


class LargestItem(BaseModel):
    path: str
    name: str
    size: int
    is_dir: bool


class RootSummary(BaseModel):
    root_path: str
    last_scanned: float | None
    total_size: int | None
    status: str
