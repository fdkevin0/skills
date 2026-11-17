#!/usr/bin/env python3
"""Validate Agent Skills frontmatter, router size budgets, JSON assets, and Markdown links."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ALLOWED_KEYS = {"name", "description", "license", "compatibility", "metadata", "allowed-tools"}
SLUG_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
INLINE_CODE_RE = re.compile(r"`[^`\n]+`")


def parse_frontmatter(text: str) -> dict[str, str]:
    """Parse minimal YAML frontmatter supporting single-line and folded/literal block scalars."""
    lines = text.splitlines()
    if len(lines) < 3 or lines[0].strip() != "---":
        raise ValueError("missing opening YAML frontmatter delimiter '---'")
    end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
    if end is None:
        raise ValueError("missing closing YAML frontmatter delimiter '---'")

    data: dict[str, str] = {}
    i = 1
    while i < end:
        line = lines[i]
        if not line.strip() or line.lstrip().startswith("#"):
            i += 1
            continue
        match = re.match(r"^([a-zA-Z0-9_-]+):\s*(.*)$", line)
        if not match:
            raise ValueError(f"unsupported frontmatter syntax at line {i + 1}: {line}")
        key, raw = match.group(1), match.group(2).strip()
        if raw in {">", ">-", "|", "|-"}:
            block: list[str] = []
            i += 1
            while i < end and (lines[i].startswith((" ", "\t")) or not lines[i].strip()):
                block.append(lines[i].strip())
                i += 1
            joiner = "\n" if raw.startswith("|") else " "
            data[key] = joiner.join(part for part in block if part).strip()
            continue
        data[key] = raw.strip("\"'")
        i += 1
    return data


def iter_markdown_links(text: str) -> list[str]:
    """Extract Markdown link targets while ignoring fenced code blocks and inline code."""
    targets: list[str] = []
    in_fence = False
    fence_marker = ""
    for line in text.splitlines():
        stripped = line.lstrip()
        if stripped.startswith(("```", "~~~")):
            marker = stripped[:3]
            if not in_fence:
                in_fence, fence_marker = True, marker
            elif marker == fence_marker:
                in_fence, fence_marker = False, ""
            continue
        if in_fence:
            continue
        cleaned = INLINE_CODE_RE.sub("", line)
        targets.extend(LINK_RE.findall(cleaned))
    return targets


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    readme_text = (root / "README.md").read_text(encoding="utf-8")
    errors: list[str] = []

    skill_dirs = sorted(p for p in (root / "skills").iterdir() if p.is_dir())
    if not skill_dirs:
        errors.append("no skills found under skills/")

    for skill_dir in skill_dirs:
        slug = skill_dir.name
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.is_file():
            errors.append(f"{slug}: missing SKILL.md")
            continue

        content = skill_md.read_text(encoding="utf-8")
        line_count = len(content.splitlines())
        if line_count > 80:
            errors.append(f"{slug}: SKILL.md has {line_count} lines (max 80 for Minimal Router)")

        try:
            fm = parse_frontmatter(content)
        except ValueError as exc:
            errors.append(f"{slug}: {exc}")
            continue

        unknown = set(fm) - ALLOWED_KEYS
        if unknown:
            errors.append(f"{slug}: disallowed frontmatter keys: {sorted(unknown)}")
        name = fm.get("name", "")
        if name != slug or not SLUG_RE.match(name) or len(name) > 64:
            errors.append(f"{slug}: invalid frontmatter name {name!r}")
        desc = fm.get("description", "")
        if not desc or len(desc) > 1024 or "Use when" not in desc:
            errors.append(f"{slug}: description must be 1..1024 chars and contain 'Use when'")
        if f"./skills/{slug}/SKILL.md" not in readme_text:
            errors.append(f"{slug}: missing entry './skills/{slug}/SKILL.md' in README.md")

    md_files = [root / "README.md", *sorted((root / "rules").glob("*.md")), *sorted((root / "skills").rglob("*.md"))]
    for md_path in md_files:
        for target in iter_markdown_links(md_path.read_text(encoding="utf-8")):
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            rel = target.split("#", 1)[0]
            if rel and not (md_path.parent / rel).resolve().exists():
                errors.append(f"{md_path.relative_to(root)}: broken link '{target}'")

    json_files = sorted((root / "skills").rglob("*.json"))
    for json_path in json_files:
        try:
            json.loads(json_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"{json_path.relative_to(root)}: invalid JSON ({exc})")

    if errors:
        for err in errors:
            print(f"ERROR: {err}", file=sys.stderr)
        return 1

    print(f"OK: validated {len(skill_dirs)} skills, {len(md_files)} markdown files, {len(json_files)} JSON files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
