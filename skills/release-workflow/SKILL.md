---
name: release-workflow
description: >-
  Prepare, land, tag, and verify a software release on repositories with
  protected main branches and immutable v* tag CI publishing. Use when cutting
  a new version release or debugging a tag-triggered release pipeline.
---

# Release Workflow (PR-First + Immutable `v*` Tag)

Cut releases via a passing PR into protected `main`, followed by either an immutable `vX.Y.Z` tag push (manual-tag repos) or merging the `release-please` PR (automated-tag repos).

## 1. Pre-Release Prep & Release PR

- **Bump & sync**: Update workspace/package manifests and lockfiles (e.g., `Cargo.toml` + `Cargo.lock`, `package.json`, `pyproject.toml`), sync versioned references in docs/container tags, and grep tests/docs for hardcoded current-version literals (prefer manifest-derived version constants and dynamic release badges so version bumps do not break CI).
- **Offline verification**: Run the full local lint, test, and doc suite using strict lockfile flags (e.g., `--locked`, `--frozen-lockfile`) before opening the PR.
- **Packaging dry-run**: When publishing packages/crates, run the ecosystem packaging dry-run (e.g., `cargo publish --dry-run --locked`) and test feature matrix variants (default vs `--no-default-features`) before opening the PR.
- **Land via PR**: Branch from `main`, commit as `chore(release): vX.Y.Z — <concise summary>`, open an English PR, pass required CI checks (and `pr-review-gate` when applicable), and squash-merge into `main` (never push release commits directly to protected `main`).
- **`release-please` repositories**:
  - Override the next version (e.g. `0.1.1` instead of `0.2.0` on `0.x.y` with `feat:` commits) via a `Release-As: X.Y.Z` commit footer, or configure `bump-minor-pre-major` + `bump-patch-for-minor-pre-major` in `release-please-config.json`.
  - If a `GITHUB_TOKEN`-authored release PR fails to trigger required `pull_request` checks (or concludes `action_required`), close and reopen it as a human (`gh pr close <N> && gh pr reopen <N>`) so CI runs before squash-merging; do not push a duplicate manual `vX.Y.Z` tag.
- **Container tag separation (when publishing to GHCR/registries)**: Reserve `:latest` and semver tags (`X.Y.Z`, `X.Y`, `X`) for release runs, publish a single rolling `:main` tag on default-branch pushes (so retention policies reap untagged manifests), and skip duplicate CI container builds on automated release commits.

## 2. Tagging Invariants (`immutable-release-tags` & Immutable Releases)

- **Sync & assert before tagging**: Run `git checkout main && git pull --ff-only` (or `git fetch origin main && git checkout --detach origin/main` inside a secondary git worktree where `main` is checked out elsewhere), then verify deterministically that `git status --porcelain` is empty, `HEAD` equals `origin/main` with green CI checks, and the version parsed from the manifest at `HEAD` equals `X.Y.Z`.
- **Treat `v*` tags and published releases as permanent**: Tag rulesets and GitHub Immutable Releases block deleting, moving, or re-uploading `v*` tags and release assets. If a defect surfaces after tagging/publishing, cut the next patch release (`vX.Y.(Z+1)`) rather than reusing the tag.
- **Create & push signed annotated tag** *(skip when `release-please` creates the tag)*:
  - `git tag -s vX.Y.Z -m "Release vX.Y.Z"` (fall back to `-a` only if signing is unavailable).
  - `git push origin vX.Y.Z`.

## 3. Post-Tag Verification

- Monitor the tag-triggered CI workflow (`gh run watch` or `gh run list --branch vX.Y.Z`) until all build, publish, and release jobs succeed.
- Confirm `gh release view vX.Y.Z` lists every release artifact and accurate release notes, and verify live published metadata (version availability, required package/lockfile contents, and provenance/attestation via `gh attestation verify` or the target registry API) across every distribution channel.
