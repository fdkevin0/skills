---
name: pr-review-gate
description: >-
  Run the single-model fresh-context PR review gate with live-boundary
  verification. Use when preparing, reviewing, or gating a PR or branch before
  merge.
---

# Single-Model Live PR Review Gate

Every non-trivial PR or branch must pass **one independent fresh-context Review Agent** auditing both static invariants and real-environment execution evidence before merge.

## 1. Reviewer Routing

- **Default (Single Fresh-Context Reviewer)**: Run one fresh-context review agent (prefer a distinct model family from the author when `codex-auth` / `agy-auth` quota permits; apply the `ponytail-review` lens for logic, security, YAGNI, and bloat).
- **High-Risk Escalation (Dual-Model)**: Add a second independent model family only when the diff touches authentication/credentials, persistent data/schema migrations, concurrency/locking primitives, or global agent instructions.

## 2. Two-Part Verification Contract

1. **SHA-Bound Runtime Evidence (`unit` + `live`)**:
   - Bind all findings and test outputs to the exact `HEAD` commit SHA (`Reviewed-SHA`).
   - Verify offline `unit` checks (`tsc`/lint/pure tests) pass cleanly.
   - Whenever the diff touches an external boundary (CLI, RPC/ACP, HTTP API, DB, auth), require real-environment verification (`live`) in an isolated temp home/namespace with `finally` cleanup—never inject production/admin secrets (such as org/admin API keys or production `.env` secrets) into automated test runs.
   - Use explicit verdicts that separate code defects from environment blocks:
     - `APPROVED` — zero static blockers and `LIVE_PASS` (or justified `LIVE_NA` for pure logic/docs-only diffs).
     - `CHANGES_REQUIRED` — correctness, security, invariant, test-hygiene, or doc-drift blocker.
     - `ENV_BLOCKED` — external `429`/`5xx`, missing isolated test account, or unavailable local binary; report the block and stop rather than mocking around it.
2. **Static Invariant & Test-Hygiene Audit**:
   - Enforce repository engineering preferences (`AGENTS.md`, `docs/preferences/`) and global agent instructions.
   - Reject AI test pathologies: module/private-prototype monkey-patching (`vi.mock`, `jest.mock`, `*.prototype.<private>`) that bypasses real wire parsers or TTLs; missing entrypoint DI seams; unisolated tests reading host `~/.gemini` or credentials; overly loose `string | object` unions hiding real display/schema fields; deleting failing tests without an explicit spec/contract change in the active task/PR; and control flow (`if`/`for`/`while`/`?:`) or sleeps in test code.
