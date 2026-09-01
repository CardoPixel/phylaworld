#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Automatic SemVer release and Conventional Changelog updater.

Invoked by .github/workflows/version-bump.yml after every merge/commit to
``main``. It finds the commits since the last release (the most recent commit
that touched ``version.json``), classifies them with the Conventional Commits
rules, computes the next SemVer version, rewrites ``version.json`` and prepends
a release section to ``CHANGELOG.md``.

Outputs (written to $GITHUB_OUTPUT when present):
  released     'true' | 'false' -- whether a new release was created
  new_version  the computed SemVer version, without a leading 'v'
"""

import json
import os
import re
import subprocess
import sys
from collections import defaultdict
from datetime import date

VERSION_FILE = "version.json"
CHANGELOG_FILE = "CHANGELOG.md"

PLAIN_SEMVER = re.compile(r"^\d+\.\d+\.\d+$")
HEADER_RE = re.compile(
    r"^(?P<type>[a-z0-9-]+)(?:\((?P<scope>[^)]+)\))?(?P<break>!)?:\s*(?P<summary>.*)$"
)
BREAKING_FOOTER_RE = re.compile(r"BREAKING[- ]CHANGE:")

# Conventional commit types -> Conventional Changelog section headings.
GROUPS = {
    "feat": "Features",
    "fix": "Bug Fixes",
    "docs": "Documentation",
    "perf": "Performance Improvements",
    "refactor": "Refactoring & Style",
    "style": "Refactoring & Style",
    "ci": "Continuous Integration",
    "build": "Build System",
    "test": "Tests",
    "chore": "Chores",
    "revert": "Reverts",
}


def git(*args):
    return subprocess.check_output(["git", *args], text=True).strip()


def read_version():
    with open(VERSION_FILE, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    if "version" not in data:
        raise ValueError("version.json must contain a 'version' key")
    return data


def write_version(data):
    with open(VERSION_FILE, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)
        fh.write("\n")


def bump(version, kind):
    """Apply a SemVer increment. While at 0.x, breaking changes bump MINOR."""
    major, minor, patch = (int(part) for part in version.split("."))
    if kind == "major":
        if major == 0:
            minor += 1
            patch = 0
        else:
            major += 1
            minor = 0
            patch = 0
    elif kind == "minor":
        minor += 1
        patch = 0
    else:  # patch
        patch += 1
    return f"{major}.{minor}.{patch}"


def last_release_commit():
    """Most recent commit that touched version.json, or None on first release."""
    out = git("log", "--format=%H", "--", VERSION_FILE)
    return out.splitlines()[0] if out else None


def collect_commits():
    since = last_release_commit()
    base = f"{since}..HEAD" if since else "HEAD"
    raw = git("log", base, "--pretty=format:%x1f%H%x1e%B")
    commits = []
    for part in raw.split("\x1f"):
        part = part.strip()
        if not part:
            continue
        sha, _, body = part.partition("\x1e")
        commits.append({"sha": sha, "body": body.strip()})
    return commits


def classify(commit):
    first = (commit["body"].splitlines() or [""])[0]
    info = {
        "sha": commit["sha"],
        "subject": first,
        "type": None,
        "scope": None,
        "summary": first,
        "breaking": bool(BREAKING_FOOTER_RE.search(commit["body"])),
        "merge": first.startswith("Merge "),
    }
    match = HEADER_RE.match(first)
    if match:
        info["type"] = match.group("type")
        info["scope"] = match.group("scope")
        info["summary"] = match.group("summary").strip()
        if match.group("break"):
            info["breaking"] = True
    return info


def entry(info):
    scope = f"**{info['scope']}:** " if info["scope"] else ""
    return f"* {scope}{info['summary']} (`{info['sha'][:7]}`)"


def render_release(version, sections):
    lines = [f"## [{version}] - {date.today().isoformat()}"]
    for heading, items in sections:
        lines.append("")
        lines.append(f"### {heading}")
        lines.extend(items)
    return "\n".join(lines)


def update_changelog(section):
    try:
        with open(CHANGELOG_FILE, "r", encoding="utf-8") as fh:
            existing = fh.read().splitlines()
    except FileNotFoundError:
        existing = []
    idx = next((i for i, line in enumerate(existing) if line.startswith("## ")), None)
    if idx is None:
        head, rest = existing, []
    else:
        head, rest = existing[:idx], existing[idx:]
    while head and not head[-1].strip():
        head.pop()
    result = head + [""] + [section] + [""] + rest
    with open(CHANGELOG_FILE, "w", encoding="utf-8") as fh:
        fh.write("\n".join(result).rstrip() + "\n")


def write_output(released, new_version):
    path = os.environ.get("GITHUB_OUTPUT")
    if path:
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(f"released={released}\n")
            fh.write(f"new_version={new_version}\n")


def main():
    data = read_version()
    current = data["version"]
    if not PLAIN_SEMVER.match(current):
        raise ValueError(
            f"version.json must contain a plain SemVer (X.Y.Z), got: {current!r}"
        )

    infos = [info for info in (classify(c) for c in collect_commits()) if not info["merge"]]
    if not infos:
        print("No releasable commits since the last release; skipping.")
        write_output("false", current)
        return

    has_breaking = any(info["breaking"] for info in infos)
    has_feature = any(info["type"] == "feat" for info in infos)
    kind = "major" if has_breaking else ("minor" if has_feature else "patch")

    new_version = bump(current, kind)
    if new_version == current:
        print("Version unchanged; nothing to do.")
        write_output("false", current)
        return

    breaking_entries = [entry(i) for i in infos if i["breaking"]]
    groups = defaultdict(list)
    for info in infos:
        groups[GROUPS.get(info["type"], "Other")].append(entry(info))

    sections = []
    if breaking_entries:
        sections.append(("Breaking Changes", breaking_entries))
    for heading, items in groups.items():
        if items:
            sections.append((heading, items))

    write_version({**data, "version": new_version})
    update_changelog(render_release(new_version, sections))

    print(f"Bumped version {current} -> {new_version}")
    write_output("true", new_version)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # noqa: BLE001 - report any failure clearly
        print(f"release.py error: {exc}", file=sys.stderr)
        sys.exit(1)