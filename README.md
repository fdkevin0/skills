# Skills

Personal collection of [Agent Skills](https://agentskills.io).

## Included Skills

| Skill | Description |
| :--- | :--- |
| [`agent-instruction-hygiene`](./skills/agent-instruction-hygiene/SKILL.md) | Author, refactor, or audit `AGENTS.md`, `SKILL.md`, and agent delegation prompts for frontier models. |
| [`github-oss-standardize`](./skills/github-oss-standardize/SKILL.md) | Audit and standardize GitHub repositories for open-source release (settings, rulesets, immutable releases, security advisories, and community health files). |
| [`pr-review-gate`](./skills/pr-review-gate/SKILL.md) | Single-model fresh-context PR review gate with SHA-bound live-boundary verification. |
| [`release-workflow`](./skills/release-workflow/SKILL.md) | Prepare, land, tag, and verify software releases on repositories with protected `main` branches and immutable `v*` tag publishing. |
| [`renovate-automerge`](./skills/renovate-automerge/SKILL.md) | Audit and configure Renovate dependency bumping with grouped schedules and risk-tiered GitHub native automerge. |
| [`test-hardening`](./skills/test-hardening/SKILL.md) | Audit, de-flake, and refactor test suites for `AGENTS.md` compliance, concurrency races, and host-state isolation. |
| [`intel-xpu`](./skills/intel-xpu/SKILL.md) | Minimal router and reference for Intel XPU GPU programming across SYCL/DPC++, Level Zero, and `torch.xpu`. |

## Global Rules

| Rule | Description |
| :--- | :--- |
| [`rules/AGENTS.md`](./rules/AGENTS.md) | Global engineering, two-tier testing, and agent delegation standards (symlinked to `~/.gemini/config/AGENTS.md`, `~/.codex/AGENTS.md`, and `~/.claude/CLAUDE.md`). |

## Install

```bash
npx skills add fdkevin0/skills -g
npx skills update -g
```
