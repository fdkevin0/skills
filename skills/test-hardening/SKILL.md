---
name: test-hardening
description: >-
  Audit, de-flake, or refactor a test suite for AGENTS.md compliance,
  concurrency races, and host-state isolation. Use when diagnosing flaky CI
  tests, auditing test hygiene, or replacing monkey-patching and sleeps with
  deterministic seams.
---

# Test Suite Hardening & Compliance Audit

Apply this workflow when diagnosing CI flakes or bringing an existing test suite into compliance with `AGENTS.md` Testing Rules.

## 1. Mechanical Audit First

Run targeted static and AST checks before reading files line-by-line so nothing slips past manual review:

- **Monkey-patching & private internals**: scan for module/SDK patchers (`vi.mock`, `jest.mock`, `mock.method`, `unittest.mock.patch`), prototype/private-field hacks, unsafe casts, and deep package-internal imports.
- **Host-state isolation**: scan offline tests for ambient environment access (`process.env`, `os.environ`, `std::env`), host home-directory lookups, and default-env client constructors that implicitly discover host binaries or credentials.
- **Sleeps & non-atomic timing**: scan for fixed sleeps/timers (`sleep`, `setTimeout`, `setInterval`), wall-clock assertions, and non-atomic fixture writes (`write` + `utimes` or in-place truncating overwrites read by active pollers).
- **In-test control flow**: parse test files via AST (or linter rules) to verify zero conditional/loop/ternary nodes inside test bodies or dynamic test-registration loops.

## 2. Expose Thin Boundary Seams (Never Patch Internals)

- Push external I/O, clock, process, and RPC boundaries to constructor or options parameters while preserving exact production defaults.
- Replace stateful branching fakes (`if (++calls === 1)`) with a linear per-call sequence double.
- Read [references/patterns.md](./references/patterns.md) when fixing filesystem pollers, multi-actor causal races, subprocess/IPC shutdown flakes, or environment leaks.

## 3. Preserve Coverage & Stress-Verify Under Hard Timeouts

- Diff all removed or renamed test titles against the base branch; never drop unique behavioral coverage while unrolling loops or deduplicating.
- Wrap multi-pass verification in hard OS timeouts (`timeout <sec> ...`) so newly introduced manual-poll deadlocks fail fast instead of hanging silently:
  - Stress changed concurrency files (`10–20x`), then run the full offline suite (`3x`) plus Tier 2 live checks.
