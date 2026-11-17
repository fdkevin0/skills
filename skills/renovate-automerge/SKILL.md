---
name: renovate-automerge
description: >-
  Audit and configure Renovate dependency bumping with grouped schedules and
  risk-tiered GitHub native automerge. Use when setting up, reviewing, or
  enabling auto-merge for dependency updates.
---

# Renovate Dependency Bump & Automerge

Inspect GitHub merge/ruleset constraints and CI coverage first, then configure `renovate.json` with grouped low-risk automerge and manual gates for high-risk or CI-uncovered updates. Use [references/renovate-baseline.json](./references/renovate-baseline.json) as the canonical starting configuration.

## 1. Pre-Flight Inspection

- **GitHub merge & ruleset readiness**: Verify `allow_auto_merge: true`, `delete_branch_on_merge: true`, and the default-branch ruleset (`required_approving_review_count: 0`, `allowed_merge_methods`, `strict_required_status_checks_policy`).
- **PR CI blind spots**: Check `.github/workflows/*.yml` to see what `pull_request` actually runs vs. `push`-only jobs (e.g., container image builds, release packaging).
- **Tool fit**: Prefer Renovate over Dependabot when syncing across toolchains, `Dockerfile`, lockfiles, and GitHub Actions; omit `.github/dependabot.yml` and keep `dependabot_security_updates` disabled when Renovate is active.

## 2. `renovate.json` Design Invariants

- **Hardened preset baseline**: Extend `["config:best-practices"]` (enables `helpers:pinGitHubActionDigests`, `docker:pinDigests`, `:configMigration`, and `abandonments:recommended` so `github-actions` and Docker receive `pinDigest`/`digest` updates); append `":preserveSemverRanges"` for published libraries that must retain manifest SemVer ranges.
- **Supply-chain cooldown & lockfile nuance**: Set `"minimumReleaseAge": "3 days"` and `"minimumReleaseAgePackageManagerSync": true`. Because `lockFileMaintenance` regenerates lockfiles via the native package manager (bypassing Renovate's per-release timestamp check and pulling un-aged transitive releases unless native cooldowns such as `pnpm` `minimumReleaseAge`, Yarn `npmMinimalAgeGate`, or `uv` `exclude-newer` are configured), keep `lockFileMaintenance.automerge: false` unless native package-manager cooldowns are active (in which case also set `"minimumReleaseAge": null` for `"matchUpdateTypes": ["lockFileMaintenance"]` in `packageRules`).
- **Native PR automerge**: Set `"platformAutomerge": true` so GitHub's native auto-merge enforces branch rulesets and status checks.
- **Explicit timezone & weekly grouping**: Declare `"timezone"` (e.g., `"Asia/Shanghai"` or `"UTC"`) instead of relying on implicit UTC. Under `strict_required_status_checks_policy: true`, group `minor`/`patch` (and `pinDigest`/`digest` for `github-actions`) updates on `"schedule": ["before 6am on monday"]` with `"automerge": true` to prevent rebase churn.
- **Manual gates & path exclusions**: Keep `"automerge": false` for `major` updates and managers uncovered by PR CI (e.g., `dockerfile`, `rust-toolchain`), and exclude `".agents/**"` (or local fixture paths) via `ignorePaths`.

## 3. Validation & Rollout

- Declare `"$schema": "https://docs.renovatebot.com/renovate-schema.json"` and validate strictly with `npx --yes --package renovate -- renovate-config-validator --strict renovate.json`.
- Land `renovate.json` via PR + squash-merge (if branch rulesets require PRs); close or manually merge pre-existing ungrouped Renovate PRs so grouped rules take over cleanly.
