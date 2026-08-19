import os
import threading
import time

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from cache import Cache, Node
from models import LargestItem, RootSummary, ScanRequest, ScanResponse, ScanStatusResponse, TreeNode
from scanner import ScanCounters, scan

load_dotenv()

DB_PATH = os.getenv("DB_PATH", "./cache.db")
DEFAULT_TREE_DEPTH = 4

app = FastAPI(
    title=os.getenv("APP_NAME", "Disk Space Analysis"),
    description="Locally-run disk space usage mapper",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # local-only tool; not exposed beyond localhost
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _db() -> Cache:
    return Cache(DB_PATH)


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.post("/api/scan", response_model=ScanResponse)
async def start_scan(req: ScanRequest):
    root_path = os.path.abspath(os.path.expanduser(req.root_path))
    if not os.path.isdir(root_path):
        raise HTTPException(status_code=400, detail=f"Not a directory: {root_path}")

    with _db() as cache:
        running = cache.get_running_scan(root_path)
        if running is not None:
            return ScanResponse(scan_id=running.id, root_path=root_path, status=running.status)
        scan_id = cache.create_scan(root_path)

    thread = threading.Thread(target=_run_scan, args=(scan_id, root_path), daemon=True)
    thread.start()

    return ScanResponse(scan_id=scan_id, root_path=root_path, status="running")


def _run_scan(scan_id: int, root_path: str) -> None:
    with _db() as cache:
        counters = ScanCounters()

        def on_progress(c: ScanCounters) -> None:
            cache.update_scan(
                scan_id, dirs_visited=c.dirs_visited, dirs_skipped=c.dirs_skipped, files_stated=c.files_stated
            )

        try:
            scan(root_path, cache, counters, on_progress=on_progress)
            cache.update_scan(
                scan_id,
                status="done",
                finished_at=time.time(),
                dirs_visited=counters.dirs_visited,
                dirs_skipped=counters.dirs_skipped,
                files_stated=counters.files_stated,
            )
        except Exception as e:  # background thread: surface the error via scan status, don't crash silently
            cache.update_scan(scan_id, status="error", finished_at=time.time(), error_message=str(e))


@app.get("/api/scan/{scan_id}/status", response_model=ScanStatusResponse)
async def scan_status(scan_id: int):
    with _db() as cache:
        s = cache.get_scan(scan_id)
    if s is None:
        raise HTTPException(status_code=404, detail="Scan not found")

    elapsed = (s.finished_at or time.time()) - s.started_at
    return ScanStatusResponse(
        scan_id=s.id,
        root_path=s.root_path,
        status=s.status,
        dirs_visited=s.dirs_visited,
        dirs_skipped=s.dirs_skipped,
        files_stated=s.files_stated,
        elapsed_seconds=elapsed,
        error_message=s.error_message,
    )


def _build_tree(cache: Cache, node: Node, depth: int) -> TreeNode:
    children: list[TreeNode] = []
    if node.is_dir and depth > 0:
        children = [_build_tree(cache, child, depth - 1) for child in cache.get_children(node.path)]
    return TreeNode(
        path=node.path,
        name=node.name,
        size=node.size,
        is_dir=node.is_dir,
        mtime=node.mtime,
        last_scanned=node.last_scanned,
        error=node.error,
        children=children,
    )


@app.get("/api/tree", response_model=TreeNode)
async def get_tree(root_path: str, depth: int = DEFAULT_TREE_DEPTH):
    root_path = os.path.abspath(os.path.expanduser(root_path))
    with _db() as cache:
        node = cache.get_node(root_path)
        if node is None:
            raise HTTPException(status_code=404, detail="No cached data for this path — scan it first")
        return _build_tree(cache, node, depth)


@app.get("/api/largest", response_model=list[LargestItem])
async def get_largest(root_path: str, kind: str = "files", limit: int = 20):
    if kind not in ("files", "dirs"):
        raise HTTPException(status_code=400, detail="kind must be 'files' or 'dirs'")
    if not 1 <= limit <= 200:
        raise HTTPException(status_code=400, detail="limit must be between 1 and 200")

    root_path = os.path.abspath(os.path.expanduser(root_path))
    with _db() as cache:
        if cache.get_node(root_path) is None:
            raise HTTPException(status_code=404, detail="No cached data for this path — scan it first")
        nodes = cache.get_largest(root_path, is_dir=(kind == "dirs"), limit=limit)
        return [LargestItem(path=n.path, name=n.name, size=n.size, is_dir=n.is_dir) for n in nodes]


@app.get("/api/roots", response_model=list[RootSummary])
async def list_roots():
    with _db() as cache:
        return [RootSummary(**r) for r in cache.list_roots()]


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
