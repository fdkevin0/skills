# Engineering & Testing Standards

- This codebase is yours: what it's for and how it's built are your call, and you'll keep building on it.
- Keep modifications elegant, concise, and maintainable long-term.
- Prefer mature libraries—especially dependencies already in the manifest—over hand-rolled parsers, CLI routers, or protocol/calendar math; disable unused default library features and delete dead shims or stale docs when retiring features.
- Validate untrusted data once at the owning boundary and pass typed values inward; query owning types/state machines for authoritative invariants and predicates rather than revalidating or re-deriving them downstream.
- Inline trivial single-use logic instead of preemptively extracting wrapper helpers; extract helpers only for reuse, genuine boundaries, or clear domain concepts that keep the main flow reading as the happy path, and keep pure parsing/validation synchronous.
- Do not silently add complexity (locks, retries, fallback layers, or speculative guards) for vanishingly unlikely race or security edge cases; surface the concrete failure mode, likelihood, and cost for buy-in first.
- Comment non-obvious constraints, invariants, or surprising behavior—never narrate obvious assignments or control flow.
- Always use English on GitHub (commits, PRs, issues, comments).
- Always keep replies concise.
- Avoid unnecessary secondary labels and descriptions; let the layout do the explaining.
- On upstream open-source repositories, defer to the target repository's `CONTRIBUTING.md` and local test conventions where they conflict with personal defaults below.

## Testing Rules

- Split verification into two tiers: **Tier 1 (`unit`)** covers pure business logic offline; **Tier 2 (`live`)** verifies external CLI/RPC/HTTP/storage boundaries against real local runtimes or isolated test accounts (HTTP VCR cassettes are optional and must scrub secrets).
- Module/SDK monkey-patching (`vi.mock`, `jest.mock`, patching private/prototype internals to invent fake service behavior) is prohibited; expose thin constructor/factory boundary seams (`CommandRunner`, loopback HTTP/stdio servers) and verify offline fixtures against real runtime payloads rather than inventing schemas.
- Ensure isolated tests sever implicit host-state, binary-discovery, and credential leaks (isolated `HOME`/`XDG_*`, minimal `PATH`, and explicit `env` injection rather than inheriting the ambient process environment).
- Test the actual implementation against concrete expected outcomes without duplicating production logic in tests; redundant tests, stub-echo assertions (merely asserting back what a fake returned), vacuous coverage-padding assertions, and change-detection tests are harmful—add regression tests only for genuine behavioral or external-contract blind spots.
- Delete or rewrite failing tests only when the active task/PR explicitly changes the requirement or external contract—never delete tests to mask regressions, and never patch around obsolete tests.
- Tests must be fully isolated; hard-coded time waits, sleeps, and timing-based concurrency stress loops are prohibited—use atomic fixture updates, deterministic event/barrier synchronization (awaiting new transitions rather than stale state), signals, or step interleaving.
- Control flow logic (conditional branches, loops, ternary expressions) is prohibited in test code; use linear assertions or per-call boundary doubles.
- Do not test frameworks, third-party libraries, or simple code without business logic.

## Agent Instructions & Delegation

- Keep `AGENTS.md` lean with contextual doc pointers (never "read X before every edit"); keep `SKILL.md` descriptions short and narrow, routing detailed workflows via progressive disclosure (`references/`).
- Reserve hard stops for irreversible or production-mutating actions; explicitly authorize safe local workflows (e.g., running disposable tests and fixing caused failures without pausing for approval).
- Proactively delegate to subagents when isolation or parallelism pays off—broad codebase exploration, noisy log/test triage, independent parallel workstreams, or fresh-context review—with self-contained prompts that return distilled summaries to protect the main context; keep trivial lookups and tightly coupled sequential edits in the main loop.
- Define end-to-end completion criteria upfront when delegating tasks so frontier models persist through implementation, verification, and failure repair instead of stopping after a first pass.
- When parallelizing subagents in a shared workspace, assign strictly disjoint file ownership and run one unified verification pass after all workers finish.
- In Antigravity (`v1.5.9` observed), keep `invoke_subagent` on `Model: "inherit"` (never `"pro"`, which server-routes to `gemini-3.8-flash-tiered`); under `Orchestrator`, dispatch reasoning-heavy subagents during Plan / `[plan review]` turns so they inherit the Carbon/Argon planner rather than the Flash execution worker (`self` subagents still get full command/write tools).
