---
name: github-oss-standardize
description: >-
  Audit and standardize a GitHub repository for open-source release (repo
  settings, branch/tag rulesets, vulnerability reporting, community health
  files, and templates). Use when open-sourcing, auditing, or standardizing a
  GitHub repository's governance and configuration.
---

# GitHub Open-Source Repository Standardization

Audit live repository state first, confirm policy choices that mutate external GitHub state, then apply settings, rulesets, and community health files end-to-end. Use [references/gh-api-and-templates.md](./references/gh-api-and-templates.md) for exact `gh api` payloads and file templates.

## 1. Read-Only Audit

Inspect live state before proposing changes:
- **Repo & merge settings**: `gh api repos/{owner}/{repo}` (merge strategies, `delete_branch_on_merge`, `allow_update_branch`, `allow_auto_merge`, `has_wiki`/`has_projects`/`has_discussions`, `security_and_analysis`, description, topics).
- **Governance & protection**: `community/profile`, `rulesets`, `branches/{default}/protection`, `private-vulnerability-reporting`, `vulnerability-alerts`, `actions/permissions/workflow`, remote branches, and active dependency bots (`renovate.json` vs `.github/dependabot.yml`).
- **Live CI check identity**: Query `commits/HEAD/check-runs` for the exact job `name` and `app.id` (GitHub Actions is `15368`)—never guess status-check context names.

## 2. Policy Baseline & Decision Boundaries

Present a concise audit gap table and confirm policy trade-offs before mutating GitHub settings. Default single-maintainer baseline:
- **Merge & features**: Squash-only (`allow_squash_merge: true`, `allow_merge_commit: false`, `allow_rebase_merge: false`), `COMMIT_OR_PR_TITLE` + `COMMIT_MESSAGES` (preserves `Co-authored-by:` trailers; `"PR_TITLE"` + `"COMMIT_MESSAGES"` fails with HTTP `422`), `delete_branch_on_merge: true`, `allow_update_branch: true`, `allow_auto_merge: true`; disable empty `Wiki`, `Projects`, and `Discussions`; delete merged stale remote branches only after `git merge-base --is-ancestor` passes; leave local agent/tooling directories untouched unless asked.
- **Rulesets (`bypass_actors: []` strict default)**:
  1. `main: PR + CI + squash` (`refs/heads/main`): block `deletion` and `non_fast_forward`, require `required_linear_history`, `pull_request` (`required_approving_review_count: 0`, `required_review_thread_resolution: true`, `allowed_merge_methods: ["squash"]`), and `required_status_checks` (`strict_required_status_checks_policy: true` with verified check context + `integration_id: 15368`).
  2. `immutable-release-tags` (`refs/tags/v*`): block `deletion`, `non_fast_forward`, and `update`.
- **Security & dependency alerts**: Enable Private Vulnerability Reporting (`PUT .../private-vulnerability-reporting`) and Vulnerability Alerts (`PUT .../vulnerability-alerts`); verify Actions default workflow permissions are `read` (`can_approve_pull_request_reviews: false`). Keep `dependabot_security_updates` disabled and omit `dependabot.yml` whenever Renovate manages dependencies.
- **Community health (`100%` target) & package metadata**:
  - Author concise English `CONTRIBUTING.md`, `SECURITY.md` (routing exclusively to `/security/advisories/new` with project-specific secret/state redaction rules), canonical Contributor Covenant v2.1 `CODE_OF_CONDUCT.md` (required for `licensee` detection), `.github/PULL_REQUEST_TEMPLATE.md`, and `.github/ISSUE_TEMPLATE/{config,bug_report,feature_request}.yml`.
  - Complete `repository` / `license` metadata in workspace manifests (`Cargo.toml`, `package.json`, `pyproject.toml`) and link governance docs from `README.md`.

## 3. Execution & End-to-End Verification

1. **Apply API settings & rulesets first**: Pass JSON via `gh api --input -` (never `-f`, which stringifies booleans/numbers/arrays) *before* merging the governance PR so the PR dogfoods the new ruleset, CI check gate, squash policy, and remote branch auto-deletion.
2. **Land files via PR**: Branch from `main`, run full offline lint/test/doc checks (`--locked`), open the PR in English, wait for CI (`gh pr checks --watch`; never shell `sleep`), and squash-merge (`gh pr merge --squash` without `--delete-branch` when `delete_branch_on_merge` is enabled, followed by `git fetch --prune`).
3. **Verify target state**: Confirm `community/profile` reports `health_percentage: 100` (note: REST leaves `issue_template: null` for YAML Issue Forms while still counting them toward `100`), both rulesets are `active`, `private-vulnerability-reporting` is `enabled: true`, and `vulnerability-alerts` returns `204`.
