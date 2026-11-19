# Deterministic Test Patterns & Concurrency Race Fixes

Recurring root causes observed in flaky CI suites and their minimal deterministic fixes.

## 1. Atomic Fixture Writes

- **Failure mode**: Writing directly to a watched target followed by `utimes` (or truncating in-place with `O_TRUNC`) races active pollers. A poll between write and `utimes` latches a fresh `mtime` prematurely; a poll mid-truncation reads an empty/partial file and drops records.
- **Fix**: Write to a sibling temp file with a non-matching extension (e.g., `.tmp` so scanners ignore it), apply metadata/timestamps to the temp file, then atomically `rename` it over the target.

## 2. Fresh-Event Barriers & In-Flight Poll Flushes

- **Failure mode A (stale predicate)**: Polling a boolean state (e.g., `waitUntil(() => !isRunning())`) during a subsequent operation returns immediately on the leftover state from an earlier operation before the new work starts.
- **Failure mode B (deduplicated poll join)**: When a manual observer deduplicates concurrent `poll()` calls behind an in-flight promise, a single `poll()` after a fixture write can join a stale pre-write read and leave a timerless loop parked forever.
- **Fix**: Synchronize on concrete new-transition events/barriers, or perform a two-step flush (drain any in-flight poll, then run one fresh post-write read).

## 3. Causal Ordering in Multi-Actor Fixtures

- **Failure mode**: Writing a terminal/completion marker before publishing the data or message it depends on lets an active observer settle early or miss payloads. Similarly, triggering follow-up state reads synchronously *inside* a hook/callback before it returns can ingest later events before the production loop arms its next phase.
- **Fix**: Publish dependent messages/data *before* writing terminal status markers, and trigger follow-up polls *after* callbacks return (e.g., signal a barrier inside the callback and flush outside).

## 4. Subprocess & IPC Shutdown Determinism

- **Failure mode A (raw EOF vs async dispatch)**: Exiting a fake stdio/RPC server synchronously on `stdin` EOF terminates before buffered async/microtask handlers dispatch preceding messages (e.g., `cancel`).
- **Failure mode B (heavy stub cold-start under tight timeouts)**: Spawning a heavy runtime script (e.g., `#!node` or `#!python`) as a fake CLI under short timeouts can hit `SIGKILL` before startup finishes writing readiness/PID markers.
- **Failure mode C (unreaped PID assertion)**: Checking `kill(pid, 0)` for `ESRCH` immediately after termination races kernel reaping (or observes a zombie process).
- **Fix**: Exit fake servers on transport/connection close rather than raw `stdin` EOF; use lightweight POSIX `#!/bin/sh` stubs (atomic PID `.tmp` + `mv`, `exec`) or compiled binaries under tight timeouts; wait via barrier for process exit/reaping (accounting for zombie state when inspecting `/proc`).

## 5. Complete Environment Isolation

- **Failure mode**: Inheriting host `PATH`, `XDG_*`, or ambient environment variables when constructing subprocesses or in-process discovery clients lets offline tests pick up host binaries, user configs, or live credentials.
- **Fix**: Construct a minimal isolated environment map (`HOME`, `XDG_CONFIG_HOME`, `XDG_CACHE_HOME`, and empty or minimal `PATH` containing only explicit test/POSIX bin dirs) and pass that exact environment to both spawned processes and in-process discovery clients.
