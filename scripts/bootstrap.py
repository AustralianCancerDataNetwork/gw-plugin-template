#!/usr/bin/env python3
"""Rename this template into a real plugin, then remove itself.

GitHub's "Use this template" copies files verbatim -- it does not substitute
anything -- so the placeholder name lands in about a dozen places. Run this
once, immediately after generating the repo:

    python3 scripts/bootstrap.py my-new-plugin --description "What it does."

Stdlib only, so it runs before `uv sync`.
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

DIST = "gw-plugin-template"
MODULE = "gw_plugin_template"
CLASS = "GwPluginTemplate"
TITLE = "Groundworkers Plugin Template"
DESCRIPTION = "Template for a Groundworkers plugin."

ROOT = Path(__file__).resolve().parent.parent
SKIP_DIRS = {".git", ".venv", "__pycache__", "dist", "build", "site", ".ruff_cache",
             ".pytest_cache", ".mypy_cache"}
SELF_DESTRUCT = ("TEMPLATE.md", "scripts/bootstrap.py")


def derive(raw: str) -> tuple[str, str, str]:
    """Return (distribution, module, ClassPrefix) from a user-supplied name."""

    slug = raw.strip().lower().replace("_", "-")
    if not re.fullmatch(r"[a-z][a-z0-9]*(-[a-z0-9]+)*", slug):
        raise SystemExit(
            f"'{raw}' is not a usable name. Use lowercase words separated by "
            "hyphens, starting with a letter, e.g. my-new-plugin."
        )
    module = slug.replace("-", "_")
    class_prefix = "".join(part.capitalize() for part in slug.split("-"))
    return slug, module, class_prefix


def text_files() -> list[Path]:
    found: list[Path] = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.relative_to(ROOT).parts):
            continue
        try:
            path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        found.append(path)
    return found


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("name", help="Distribution name, e.g. my-new-plugin")
    parser.add_argument("--title", default=None, help="Human-readable title")
    parser.add_argument("--description", default=None, help="One-line summary")
    parser.add_argument(
        "--dry-run", action="store_true", help="Show what would change"
    )
    args = parser.parse_args(argv)

    dist, module, class_prefix = derive(args.name)
    if dist == DIST:
        raise SystemExit("Choose a name other than the template's own.")

    title = args.title or " ".join(p.capitalize() for p in dist.split("-"))
    description = args.description or f"Groundworkers plugin: {title}."

    replacements = (
        (MODULE, module),
        (DIST, dist),
        (CLASS, class_prefix),
        (TITLE, title),
        (DESCRIPTION, description),
    )

    changed = 0
    for path in text_files():
        original = path.read_text(encoding="utf-8")
        updated = original
        for old, new in replacements:
            updated = updated.replace(old, new)
        if updated != original:
            changed += 1
            if args.dry_run:
                print(f"  would rewrite {path.relative_to(ROOT)}")
            else:
                path.write_text(updated, encoding="utf-8")

    package = ROOT / "src" / MODULE
    target = ROOT / "src" / module
    if package.exists():
        if args.dry_run:
            print(f"  would rename src/{MODULE} -> src/{module}")
        else:
            package.rename(target)

    for relative in SELF_DESTRUCT:
        path = ROOT / relative
        if not path.exists():
            continue
        if args.dry_run:
            print(f"  would delete {relative}")
        else:
            path.unlink()
    scripts = ROOT / "scripts"
    if not args.dry_run and scripts.is_dir() and not any(scripts.iterdir()):
        shutil.rmtree(scripts)

    if args.dry_run:
        print(f"\nDry run: {changed} file(s) would be rewritten.")
        return 0

    print(f"Renamed to {dist} ({changed} file(s) rewritten).\n")
    print("Next:")
    print("  1. uv sync --all-extras --dev && uv run pytest -q")
    print("  2. git config core.hooksPath .githooks")
    print("  3. Rename the classes and tools to match what your plugin does.")
    print("  4. Apply the repo settings a template does NOT copy:")
    print("     labels, the main ruleset, the pypi environment, and the")
    print("     PyPI trusted publisher. See the cava-devops setup guide:")
    print("     https://australiancancerdatanetwork.github.io/cava-devops/guides/setup-new-repo/")
    print("  5. Commit on a branch and open a PR labelled 'chore'.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
