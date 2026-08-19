# Roadmap

## Vision

A locally-run Vite + React app that gives real insight into where disk space
is going under `~` — by directory and by file type/size — and that can act on
that insight directly: deleting or moving files without leaving the app.

Everything shipped so far is read-only. Deleting and moving are the main
missing pieces and, because they touch the real filesystem, they're being
built last and carefully rather than bolted on quickly.

## Status

### Phase 1 — Home-directory insight polish — **done**

- Default/shortcut to scan `~` (`App.tsx`'s "Scan Home (~)" button; the
  backend already expanded `~` server-side via `os.path.expanduser`)
- File-type categories expanded from 3 (Video/Photos/Other) to 7
  (+ Documents, Audio, Archives, Apps), each with a validated categorical
  color (`frontend/src/lib/fileCategory.ts`)
- "Largest files" / "largest directories" tables, ranked across the full
  scanned subtree via a recursive SQL query (`backend/cache.py:get_largest`,
  `GET /api/largest`) — not limited by the treemap's rendering depth cap

No filesystem mutation risk in this phase; it was all read/query-side.

### Phase 2 — Safe delete — **planned, not started**

- Backend: `DELETE /api/node` moves the target to macOS Trash (via
  `send2trash`, not `os.remove`/`shutil.rmtree`) — **decided: Trash, not
  permanent delete**, since this tool will be pointed at `~` and a wrong
  target should be recoverable from Finder
- Restricted to paths under a root that's actually been scanned (no
  arbitrary filesystem access from the API)
- UI: a delete action per treemap tile / largest-item row, with a
  confirmation dialog before the request fires
- Cache: on success, drop the node's subtree from the cache and refresh the
  parent's aggregate size without a full rescan

### Phase 3 — Move

- Backend: `POST /api/node/move` (`shutil.move`)
- UI: destination picker (path input, or a drag target on the treemap) and a
  move action per node
- Conflict handling when the destination already exists
- Cache invalidation for both the source and destination subtrees

### Phase 4 — Guardrails

- Path validation: no escaping the scanned root, no system paths (e.g. deny
  `/System`, `/Library` outside the user's own home)
- Undo affordance where feasible (Trash already gives this for deletes)
- A dry-run / "what would be deleted" summary before committing on a
  directory, not just a single file

## Testing gaps to close

Not phase-gated — pick up alongside whichever phase is active, or as its own
pass. See the README's Testing section for the current state. Priority order:

1. `App.tsx` — the scan → poll → load-tree → error-handling flow has zero
   test coverage today despite being the main thing a user actually drives.
   Highest priority once Phase 2/3 add mutating actions here, since those
   will land in this same file.
2. `lib/format.ts` (`formatBytes`) — small, pure, easy to verify, currently
   untested unit-boundary math (KB/MB/GB rollover).
3. Remaining display components (`BreakdownBar`, `Breadcrumb`, `RootsList`,
   `LargestList`) — no rendering tests yet.
4. `lib/api.ts` — fetch wrappers and error-body parsing untested.
5. Wire up `pytest-cov` (backend) and `@vitest/coverage-v8` (frontend) so
   coverage is a measured number instead of a file-by-file read.

## Explicitly out of scope for now

- Duplicate-file detection
- Cloud storage / non-local filesystems
- Multi-user / remote access — this stays a `localhost`-only tool
