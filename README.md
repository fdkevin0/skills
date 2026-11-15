# Skills

Personal collection of [Agent Skills](https://agentskills.io).

## Included Skills

| Skill | Description |
| :--- | :--- |
| [`agent-instruction-hygiene`](./skills/agent-instruction-hygiene/SKILL.md) | Author, refactor, or audit `AGENTS.md`, `SKILL.md`, and agent delegation prompts for frontier models. |
| [`pr-review-gate`](./skills/pr-review-gate/SKILL.md) | Single-model fresh-context PR review gate with SHA-bound live-boundary verification. |
| [`intel-xpu`](./skills/intel-xpu/SKILL.md) | Intel XPU GPU programming reference covering SYCL/DPC++, `torch.xpu`, and Level Zero. |

## Global Rules

| Rule | Description |
| :--- | :--- |
| [`rules/AGENTS.md`](./rules/AGENTS.md) | Global engineering, two-tier testing, and agent delegation standards (symlinked to `~/.gemini/config/AGENTS.md`, `~/.codex/AGENTS.md`, and `~/.claude/CLAUDE.md`). |

## Install

```bash
npx skills add fdkevin0/skills -g
npx skills update -g
```
