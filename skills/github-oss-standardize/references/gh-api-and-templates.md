# GitHub API Payloads & Governance Templates

Replace `$REPO` (`owner/name`) and `$CHECK_CONTEXT` (verified from `commits/HEAD/check-runs`) before running.

## 1. Read-Only Audit Commands

```bash
REPO="owner/name"
gh api "repos/$REPO" --jq '{description,homepage,topics,has_issues,has_projects,has_wiki,has_discussions,allow_squash_merge,allow_merge_commit,allow_rebase_merge,allow_auto_merge,delete_branch_on_merge,allow_update_branch,squash_merge_commit_title,squash_merge_commit_message,security_and_analysis}'
gh api "repos/$REPO/community/profile"
gh api "repos/$REPO/rulesets"
gh api "repos/$REPO/actions/permissions/workflow"
gh api "repos/$REPO/private-vulnerability-reporting"
gh api -i "repos/$REPO/vulnerability-alerts" | head -n 5
gh api "repos/$REPO/commits/HEAD/check-runs" --jq '.check_runs[] | {name, app_id: .app.id, app_slug: .app.slug}'
gh api "repos/$REPO/branches" --jq '.[].name'
```

## 2. Repository Settings, Security & Ruleset Payloads

### Merge & Feature Settings (`PATCH`)

Valid `(squash_merge_commit_title, squash_merge_commit_message)` pairs in GitHub's REST API:
- `("COMMIT_OR_PR_TITLE", "COMMIT_MESSAGES")` — preserves commit summaries and `Co-authored-by:` trailers (default)
- `("PR_TITLE", "PR_BODY")`
- `("PR_TITLE", "BLANK")`

```bash
gh api --method PATCH "repos/$REPO" --input - <<'EOF'
{
  "has_wiki": false,
  "has_projects": false,
  "has_discussions": false,
  "allow_squash_merge": true,
  "allow_merge_commit": false,
  "allow_rebase_merge": false,
  "squash_merge_commit_title": "COMMIT_OR_PR_TITLE",
  "squash_merge_commit_message": "COMMIT_MESSAGES",
  "delete_branch_on_merge": true,
  "allow_update_branch": true,
  "allow_auto_merge": true
}
EOF
```

### Private Vulnerability Reporting & Vulnerability Alerts (`PUT`)

```bash
gh api --method PUT "repos/$REPO/private-vulnerability-reporting"
gh api --method PUT "repos/$REPO/vulnerability-alerts"
```

### Branch Ruleset (`main: PR + CI + squash`)

For admin PR-only bypass instead of strict zero-bypass, set `"bypass_actors": [{"actor_id": 5, "actor_type": "RepositoryRole", "bypass_mode": "pull_request"}]`.

```bash
gh api --method POST "repos/$REPO/rulesets" --input - <<'EOF'
{
  "name": "main: PR + CI + squash",
  "target": "branch",
  "enforcement": "active",
  "conditions": {
    "ref_name": {
      "exclude": [],
      "include": ["refs/heads/main"]
    }
  },
  "bypass_actors": [],
  "rules": [
    { "type": "deletion" },
    { "type": "non_fast_forward" },
    { "type": "required_linear_history" },
    {
      "type": "pull_request",
      "parameters": {
        "required_approving_review_count": 0,
        "dismiss_stale_reviews_on_push": false,
        "required_reviewers": [],
        "require_code_owner_review": false,
        "require_last_push_approval": false,
        "required_review_thread_resolution": true,
        "allowed_merge_methods": ["squash"]
      }
    },
    {
      "type": "required_status_checks",
      "parameters": {
        "strict_required_status_checks_policy": true,
        "do_not_enforce_on_create": false,
        "required_status_checks": [
          {
            "context": "check",
            "integration_id": 15368
          }
        ]
      }
    }
  ]
}
EOF
```

### Tag Ruleset (`immutable-release-tags`)

```bash
gh api --method POST "repos/$REPO/rulesets" --input - <<'EOF'
{
  "name": "immutable-release-tags",
  "target": "tag",
  "enforcement": "active",
  "conditions": {
    "ref_name": {
      "exclude": [],
      "include": ["refs/tags/v*"]
    }
  },
  "bypass_actors": [],
  "rules": [
    { "type": "deletion" },
    { "type": "non_fast_forward" },
    { "type": "update" }
  ]
}
EOF
```

## 3. Governance & Template Skeletons

Adapt commands, runtime flags, and sensitive-artifact redaction lists to the target repository.

### `CONTRIBUTING.md`

```markdown
# Contributing

Bug reports, documentation improvements, and focused pull requests are welcome.
For larger architectural or protocol changes, open an issue first to agree on
the problem and scope.

All participation is governed by the [code of conduct](CODE_OF_CONDUCT.md).
Report security vulnerabilities through the [security policy](SECURITY.md)
instead of public issues or pull requests.

## Development

Before opening a pull request, run:

<!-- Replace with exact project offline check commands -->

Add regression tests for behavior changes and update relevant documentation.
Keep code, comments, commit messages, documentation, issues, and pull requests
in English. Never include credentials, tokens, or private state in code, logs,
or fixtures.

## Pull requests

Create a branch from `main` and keep each pull request focused on one logical
change. Explain the problem, resulting behavior, and validation performed. All
changes to `main` go through a pull request with passing CI and resolved review
discussions. A second person's approval is not required for this
single-maintainer project, and pull requests are squash merged.
```

### `SECURITY.md`

```markdown
# Security policy

Security fixes target the latest published release and `main`. Upgrade before
checking whether an issue still reproduces.

## Reporting a vulnerability

Use [GitHub private vulnerability reporting](https://github.com/<owner>/<repo>/security/advisories/new).
Do not disclose vulnerabilities in public issues or pull requests.

Include the affected version or commit SHA, reproduction steps, expected and
actual behavior, and potential impact. Scrub credentials, tokens, and private
state from logs or examples.

This project is maintained by one person; response times are best effort.
```

### `.github/PULL_REQUEST_TEMPLATE.md`

```markdown
## Problem and change

<!-- Explain the problem and resulting behavior. Link an issue if relevant. -->

## Validation

<!-- List checks performed and their results, including any checks not run. -->

- [ ] `<lint / format check>`
- [ ] `<unit / integration tests>`
- [ ] `<package / doc / live boundary check if applicable>`
```

### `.github/ISSUE_TEMPLATE/config.yml`

```yaml
blank_issues_enabled: true
contact_links:
  - name: Report a security vulnerability
    url: https://github.com/<owner>/<repo>/security/advisories/new
    about: Report vulnerabilities privately; do not open a public issue.
```

### `.github/ISSUE_TEMPLATE/bug_report.yml` & `feature_request.yml`

- `bug_report.yml`: Top markdown sanitization banner (never paste credentials/tokens/private state; route vulnerabilities via Security tab), required environment/version field, required reproduction steps, required expected vs actual behavior, optional sanitized logs.
- `feature_request.yml`: Required `What problem would this solve?` and `Suggested solution and alternatives` textareas.
- `CODE_OF_CONDUCT.md`: Use the canonical **Contributor Covenant v2.1** English text (required for GitHub `licensee` detection) with `## Enforcement` pointing to private advisory reporting or maintainer GitHub profile.
