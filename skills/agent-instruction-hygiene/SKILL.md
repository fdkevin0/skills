---
name: agent-instruction-hygiene
description: >-
  Author, refactor, or audit AGENTS.md, SKILL.md, and agent delegation prompts
  for frontier models (GPT-6 Astra, Gemini 4). Use when creating or reviewing
  skills, repository rules, or automated delegation prompts.
---

# Frontier Agent Instruction Hygiene

Apply these four principles when writing or auditing `SKILL.md`, `AGENTS.md`, or delegated agent prompts.

## 1. Lean, High-Signal Skills (`SKILL.md`)

- **Narrow trigger descriptions**: Keep `description` as short as possible and specify exact trigger actions rather than broad domain keywords (prevents description truncation and false-positive loading).
  - *Avoid*: `Use when working with databases, queries, models, or persistence.`
  - *Prefer*: `Use when adding, changing, or reviewing a schema migration.`
- **Progressive disclosure (Minimal Router)**: For multi-workflow skills, keep root `SKILL.md` as a concise router linking to `references/` and `scripts/` so the model reads only what applies to the active task.
- **Invariants over rigid recipes**: Avoid over-prescribing step-by-step itineraries where modern models handle nuance well; capture non-obvious environment quirks, constraints, and verification invariants without overconstraining stronger models.

## 2. Contextual `AGENTS.md`

- **Route docs by context, never "before every edit"**: Never force upfront full-repo reading stacks (`Before every edit, read X, Y, Z`). Map docs to when they apply (`Use architecture.md for service boundaries, api.md for Hub REST endpoints`).
- **Drop generic handholding; grant explicit safe autonomy**: Frontier models run checks naturally—avoid generic nagging to test. Instead, explicitly state safe local execution boundaries so tentative models keep going without unnecessary approval stops:
  > *Example*: Local tests use disposable fixtures with no production access; run them, fix failures caused by your change, and rerun affected tests without pausing for approval.
- **Prune cleanly (zero transitional residue)**: Delete outdated guardrails, state only the target invariant (avoid "no legacy-X" negations), and grep sibling `AGENTS.md` / `README.md` / `docs/` to clear dangling references.

## 3. Calibrated Decision Boundaries

- **State real safety boundaries, not alarmist stop-signs**: Aligned frontier models take defensive "always stop and ask first" rules literally and halt prematurely on safe work. Reserve hard stops strictly for irreversible, external, or credential/production-mutating actions.

## 4. Explicit Completion & Persistence (Delegation Prompts)

- **Define "done" upfront**: Frontier models like GPT-6 Astra may stop after a first pass for review unless told how far to carry the task. Explicitly specify end-to-end completion criteria (e.g., implement, run verification, inspect output, fix caused failures, and reach target state).
- **Eliminate unintended mid-flight checkpoints**: Do not ask for intermediate review pauses unless human sign-off is genuinely required before the next step.
