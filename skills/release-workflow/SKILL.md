---
name: release-workflow
description: >-
  Prepare, land, tag, and verify a software release on repositories with
  protected main branches and immutable v* tag CI publishing. Use when cutting
  a new version release or debugging a tag-triggered release pipeline.
---

# Release Workflow (PR-First + Immutable `v*` Tag)

Cut releases in two phases: land version/doc updates on `main` via a passing PR, then push a signed annotated `vX.Y.Z` tag to trigger automated publishing.

## 1. Pre-Release Prep & Release PR

- **Bump & sync**: Update workspace/package manifests and lockfiles (e.g., `Cargo.toml` + `Cargo.lock`, `package.json`, `pyproject.toml`) and sync versioned references in docs, container tags, or third-party notices.
- **Offline verification**: Run the full local lint, test, and doc suite using strict lockfile flags (e.g., `--locked`, `--frozen-lockfile`) before opening the PR.
- **Packaging dry-run**: When publishing packages/crates, run the ecosystem packaging dry-run (e.g., `cargo publish --dry-run --locked`) and test feature matrix variants (default vs `--no-default-features`) before opening the PR.
- **Land via PR**: Branch from `main`, commit as `chore(release): vX.Y.Z — <concise summary>`, open an English PR, pass required CI checks (and `pr-review-gate` when applicable), and squash-merge into `main` (never push release commits directly to protected `main`).

## 2. Tagging Invariants (`immutable-release-tags` & Immutable Releases)

- **Sync & assert before tagging**: Run `git checkout main && git pull --ff-only` (or `git fetch origin main && git checkout --detach origin/main` inside a secondary git worktree where `main` is checked out elsewhere), then verify deterministically that `git status --porcelain` is empty, `HEAD` equals `origin/main` with green CI checks, and the version parsed from the manifest at `HEAD` equals `X.Y.Z`.
- **Treat `v*` tags and published releases as permanent**: Tag rulesets and GitHub Immutable Releases block deleting, moving, or re-uploading `v*` tags and release assets. If a defect surfaces after tagging/publishing, cut the next patch release (`vX.Y.(Z+1)`) rather than reusing the tag.
- **Create & push signed annotated tag**:
  - `git tag -s vX.Y.Z -m "Release vX.Y.Z"` (fall back to `-a` only if signing is unavailable).
  - `git push origin vX.Y.Z`.

## 3. Post-Tag Verification

- Monitor the tag-triggered CI workflow (`gh run watch` or `gh run list --branch vX.Y.Z`) until all build, publish, and release jobs succeed.
- Confirm `gh release view vX.Y.Z` lists every artifact declared by the release workflow (archives, checksums/`SHA256SUMS`, container images, or registry packages) and accurate release notes; when build provenance or immutable releases are enabled, verify artifact provenance via `gh attestation verify <artifact> --repo <owner>/<repo>`.
