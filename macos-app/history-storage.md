# Storing time-series history

## Overview

An app can record a sample every few seconds for weeks and show it in a window and in a CLI. Then the number of pages that each commit changes sets the disk writes, not the number of rows. macOS writes a "disk writes" diagnostic report for a process that dirties more than 2 147 MB in 24 h (about 24.9 KB/s).

## One writer, many readers

1. One process writes the file. If the data needs more rights than the user has, that process is a root LaunchDaemon (a background job that starts at boot). The app and the CLI never write; they ask it over XPC (the macOS inter-process channel) for live data and actions.
2. The writer opens with `journal_mode=WAL` and `synchronous=NORMAL`. A reader opens the file read-only (`SQLITE_OPEN_READONLY`; in a shell, `sqlite3 -readonly`) with a busy timeout of 5 s. WAL lets readers run while the writer writes.
3. Set `auto_vacuum=INCREMENTAL` before the first table exists. It has no effect later.
4. If the file is corrupt, move it and its `-wal` and `-shm` files aside as `<path>.corrupt-<unix ts>` and open a new one once, not an exit loop. Store times as Unix seconds in UTC.

## Schema

- `processes(id, pid, start_time, ..., first_seen, last_seen)` with `UNIQUE(pid, start_time)`. PIDs are reused, so the identity is `(pid, start_time)`.
- Group by the responsible process (the app that launched a helper), not by the parent. Skip terminal apps, or every shell command groups under the terminal. Fall back to the outermost `.app` on the path. The private call is a known risk (`process-inspection.md`).
- Sample tables are keyed time first and `WITHOUT ROWID`: `PRIMARY KEY(ts, process_id)`. A tick then appends at the right edge and retention deletes at the left edge. No index or foreign key starts with `process_id`: it puts each row of a tick on a different page.
- Tiers: raw, minute, hour. A rollup row holds avg and max per metric, key `(bucket, process_id)`. System rows stay dense, one per bucket.

## Sparse rows and carry-forward

- Write a process row only when a metric moved past a jitter threshold, or when a heartbeat expired (raw 60 s, minute tier 60 min, hour tier 24 h). About 94 % of processes are idle. Dense storage measured about 6.5 GB for 0.7 GB sparse.
- A reader must never assume a row per bucket. A row holds from its time until the next row or `last_seen`. Cap the hold: 65 s raw, 3660 s minute, 90 000 s hour. A longer gap means the process ended or the Mac slept, so the row held one tick.
- Read from `start - hold`, or the first slice of the window is empty.
- Compute each tier from the raw hold segments, not from the tier below.
- Do not update `last_seen` for each live process each minute. Keep it open (`9e999`) while the process lives. A reader maps open to the writer's last tick, taken from the system table. A new writer first closes processes that the old one left open.

## Commit, checkpoint, retention

- Commit every 3 ticks (a row reaches the file up to 10 s late; a crash loses up to 2 ticks). Checkpoint every 5 min with `wal_autocheckpoint=0` (a power loss can lose up to 5 min). Measured, with 1 500 live processes and 2 700 new per hour: 359 KB/s before, 13.6 KB/s after.
- The checkpoint waits 100 ms for readers, not the full busy timeout, or it blocks the writer queue. Log a busy result; the WAL grows until one succeeds.
- Retention: raw 24 h, minute 30 days, hour 90 days, plus a size cap that drops the finest rolled-up tier first. Never delete raw rows that a tier has not rolled up yet (keep 65 s before the oldest watermark).
- Roll up each minute on the writer's serial queue after the write. A bucket is complete only 65 s after its end.
- Keep up to 8 MB of free pages for the next inserts and run `incremental_vacuum` only on the excess. Vacuuming all of it moves pages that the next ticks fill again.

## What the UI and CLI read

- Per range, pick the tier: raw for hours, minute for days, hour for weeks. Fill carry-forward in the reader.
- Process lists by `last_seen > start AND first_seen < end`.
- Mark a process "exited" when `last_seen < now - exitSlack`. Derive it: `60 + tick * (ticksPerCommit + 1) + 5`. A fixed 70 s flashed live processes as exited.

## Traps

| Symptom | Cause | Fix |
|---|---|---|
| Daemon near the macOS disk-write limit (600 KB/s measured) | One commit each tick; indexes on `process_id`; `last_seen` updates | Time-first `WITHOUT ROWID`, batch commits, checkpoint every 5 min |
| 24.9 KB/s at 10 000 new processes/h | The `processes` table (one new row each) | Accept at the real load; measure 24 h live; trigger a table fix above 20 KB/s |
| Live process flashes "Exited" about once a minute | Commit lag of 10 s used up the 70 s margin | Derive the slack from the cadence |
| Free pages return after each vacuum | Vacuum took the pages the next ticks need | Vacuum only the excess over a reserve |
| Live view stalls at a checkpoint | `TRUNCATE` waited for a reader on the shared queue | 100 ms busy timeout during the checkpoint |

## Common mistakes

| Mistake | Reality |
|---|---|
| Key the process by `pid` | PIDs are reused. Use `(pid, start_time)`. |
| Add an index on `process_id` for speed | It costs a page for each row of a tick. Read through the time key. |
| Optimize rows written | Pages changed per commit set the bytes written. |
| Let the app open the file for writing | Two writers break the disk budget. Use XPC. |
