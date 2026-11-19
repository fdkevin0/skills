---
name: pr-review-gate
description: >-
  Run the single-model fresh-context PR review gate with live-boundary
  verification. Use when preparing, reviewing, or gating a PR or branch before
  merge.
---

# Single-Model Live PR Review Gate

Every non-trivial PR or branch requires sign-off from **one fresh-context Review Agent** before merge.

## 1. Dispatch

- **Antigravity**: Launch one fresh-context subagent via `invoke_subagent` (`TypeName: "self"`, `Model: "inherit"`; under `Orchestrator`, dispatch during the Plan / Plan Review turn so `inherit` binds to the Carbon/Argon planner rather than the Flash execution worker).
- **Other harnesses (`paseo` / CLI)**: Run one fresh-context review session on the active default frontier model.
- **Review scope**: Read-only against repository files; audit logic, security, load behavior, YAGNI (`ponytail-review` lens), and compliance with global/repo `AGENTS.md` and `docs/preferences/`.
- **Cleanup & schema checks**: Flag hand-rolled wheels replaceable by mature/existing deps, leftover dead types/docs from retired features, stub-echo tests, and offline fixtures whose shape diverges from live external payloads.

## 2. Verification & Verdict Contract

- **Bind to `HEAD`**: Record the exact commit SHA (`Reviewed-SHA`) for all checks and findings.
- **Run both tiers**:
  - `Tier 1 (unit)`: Offline typecheck, lint, and pure unit tests pass, with no banned test anti-patterns from `AGENTS.md`.
  - `Tier 2 (live)`: When the diff crosses an external boundary (CLI, RPC/ACP, HTTP, DB, auth), verify both happy paths and adversarial edge cases (missing entries, tie-breaks, case/encoding mismatches, malformed inputs) against the real local runtime or isolated test account in a temp home/namespace with teardown—never pass production or org/admin secrets.
- **Emit one verdict**:
  - `APPROVED` — zero blockers and `LIVE_PASS` (or justified `LIVE_NA` for pure logic/docs).
  - `CHANGES_REQUIRED` — correctness, security, invariant, test-hygiene, bloat, or doc-drift blocker.
  - `ENV_BLOCKED` — external `429`/`5xx`, missing isolated test account, or unavailable local runtime; report and stop rather than mocking around it.
