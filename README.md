# disk-space-analysis

The goal of this project is to comprehensively map out disk space usage —
starting with read-only insight into where space is going under your home
directory, eventually extending to safely deleting or moving files directly
from the app. See [ROADMAP.md](ROADMAP.md) for what's done and what's next.

A locally-run web app that scans a directory tree and renders it as a
treemap, so you can see what's actually taking up space. Rescans are
incremental — a directory whose contents haven't changed since the last scan
is skipped rather than re-walked, so repeat scans of a large tree are fast.

## Features

- **Treemap visualization** — drill into any directory, tiles sized by bytes
- **File-type breakdown** — every file is bucketed into one of 7 categories
  (Video, Photos, Documents, Audio, Archives, Apps, Other) by extension, shown
  as a stacked bar and as treemap tile color, both computed client-side from
  the fetched tree (see `frontend/src/lib/fileCategory.ts`)
- **Largest files / largest directories** — ranked across the *entire*
  scanned subtree (not capped by the treemap's rendering depth), via a
  recursive SQL query against the cache (`backend/cache.py:get_largest`)
- **Scan Home (~)** shortcut, plus a free-text path input for any directory
- **Previously scanned roots** list for quick re-entry without rescanning
- **Incremental rescans** — see "How the incremental scan works" below

Not yet built: deleting or moving files from the app. Everything today is
read-only. See [ROADMAP.md](ROADMAP.md) for the plan to add that safely.

## Stack

- **Backend**: Python (FastAPI) + SQLite, `backend/`
- **Frontend**: TypeScript React (Vite) + d3-hierarchy treemap, `frontend/`

## Running locally

Two terminals:

```bash
cd backend && ./init.sh && ./run.sh    # http://localhost:8001
```

```bash
cd frontend && ./init.sh && ./run.sh   # http://localhost:5174
```

Open http://localhost:5174, either click **Scan Home (~)** or enter a
directory path (e.g. `/Users/you/Downloads`) and click **Scan**.

Note: ports 8001/5174 were chosen instead of the usual 8000/5173 because
those were already in use by another local project's dev servers.

## API

All endpoints are served by the backend at `http://localhost:8001`:

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Liveness check |
| POST | `/api/scan` | Start (or resume) a scan of `root_path`; returns a `scan_id` |
| GET | `/api/scan/{scan_id}/status` | Poll scan progress (`running`/`done`/`error`) |
| GET | `/api/tree` | Cached tree for `root_path`, capped at `depth` levels (default 4) |
| GET | `/api/largest` | Top `limit` files or directories (`kind=files\|dirs`) under `root_path`, any depth |
| GET | `/api/roots` | Every previously scanned root with its latest status and total size |

## Testing

```bash
cd backend  && ./run.sh test   # pytest
cd frontend && ./run.sh test   # vitest
```

**Backend** — thorough on the hard parts: `scanner.py` (incremental
skip/rescan, symlinks, permission errors, add/remove/edit detection) and
`cache.py` (CRUD, reconciliation, the largest-items query) each have a full
unit suite; `main.py`'s API layer is covered for happy paths and the main
error cases (404/400s, resuming an already-running scan).

**Frontend** — the pure-logic modules are well tested (`lib/fileCategory.ts`,
`lib/treemap.ts`, the `Treemap` component). Everything else — `App.tsx`'s
scan/poll/error orchestration, the other display components
(`BreakdownBar`, `Breadcrumb`, `RootsList`, `LargestList`), `lib/api.ts`, and
`lib/format.ts` — currently has no dedicated tests. Neither project has
coverage tooling wired up (`pytest-cov` / `@vitest/coverage-v8`), so this is
a qualitative read, not a measured percentage. See ROADMAP.md for the
prioritized list to close these gaps.

## How the incremental scan works

A directory's own mtime changes only when a direct child is added, removed,
or renamed — never when a file deeper in the tree is edited, and it never
propagates to ancestor directories. So a rescan skips re-listing any
directory whose mtime hasn't changed, but always recurses into every
subdirectory (a change could be nested arbitrarily deep without touching a
parent's mtime). Known limitation: a file rewritten in place with identical
size and mtime looks unchanged to the scanner.

See `backend/scanner.py` for the implementation and `backend/tests/test_scanner.py`
for the regression test covering this behavior.
