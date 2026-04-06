#!/usr/bin/env python3
"""
AST-based import boundary checker for Phoenix Core canonical Python trees.

Forbidden top-level package roots (first segment of imported module):
  legacy, experimental, server

Scanned roots (relative to repo): backend/, desktop/, packages/, tests/
Excluded: experimental/, legacy/ (by path prefix under repo root)
"""
from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

FORBIDDEN_ROOTS = frozenset({"legacy", "experimental", "server"})
SCAN_DIRS = ("backend", "desktop", "packages", "tests")
SKIP_PATH_PARTS = frozenset(
    {
        "experimental",
        "legacy",
        "node_modules",
        ".git",
        "dist",
        "build",
        "__pycache__",
    }
)

ALLOW_RE = re.compile(r"#\s*import-boundary:\s*allow\s+(.+?)\s*$")


def _first_segment(mod: str) -> str:
    return mod.split(".", 1)[0] if mod else ""


def imports_in_file(path: Path) -> list[tuple[int, str, str]]:
    """Return list of (lineno, kind, module) for import/from nodes."""
    try:
        src = path.read_text(encoding="utf-8")
    except OSError as e:
        return [(0, "error", str(e))]
    try:
        tree = ast.parse(src, filename=str(path))
    except SyntaxError as e:
        return [(e.lineno or 0, "syntax", str(e))]

    out: list[tuple[int, str, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                out.append((node.lineno, "import", alias.name))
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                out.append((node.lineno, "from", node.module))
            elif node.level:
                # relative import — allow
                pass
    return out


def _allowed_for_line(src_lines: list[str], lineno: int, imported: str) -> bool:
    """
    Return True if the given import is explicitly allowed on this line.

    Syntax (on the same line as the import):
      # import-boundary: allow server
      # import-boundary: allow server.api
      # import-boundary: allow *
    """
    if lineno <= 0 or lineno > len(src_lines):
        return False
    line = src_lines[lineno - 1]
    m = ALLOW_RE.search(line)
    if not m:
        return False
    allow_expr = m.group(1).strip()
    if allow_expr == "*":
        return True
    imported = imported.strip()
    root = _first_segment(imported)
    if allow_expr == root or imported == allow_expr or imported.startswith(allow_expr + "."):
        return True
    return False


def should_skip(path: Path, root: Path) -> bool:
    rel = path.relative_to(root)
    for part in rel.parts:
        if part in SKIP_PATH_PARTS:
            return True
    return False


def main() -> int:
    repo = Path(__file__).resolve().parent.parent
    violations: list[str] = []

    for dirname in SCAN_DIRS:
        base = repo / dirname
        if not base.is_dir():
            continue
        for path in base.rglob("*.py"):
            if should_skip(path, repo):
                continue
            try:
                src_lines = path.read_text(encoding="utf-8").splitlines()
            except OSError as e:
                violations.append(f"{path.relative_to(repo)}:0: error: {e}")
                continue
            for lineno, kind, mod in imports_in_file(path):
                if kind in ("error", "syntax"):
                    violations.append(f"{path.relative_to(repo)}:{lineno}: {kind}: {mod}")
                    continue
                seg = _first_segment(mod)
                if seg in FORBIDDEN_ROOTS:
                    if _allowed_for_line(src_lines, lineno, mod):
                        continue
                    violations.append(
                        f"{path.relative_to(repo)}:{lineno}: forbidden {kind} '{mod}' "
                        f"(cannot import from '{seg}' in canonical tree)"
                    )

    if violations:
        print("IMPORT BOUNDARY VIOLATIONS:\n", file=sys.stderr)
        for v in violations:
            print(v, file=sys.stderr)
        return 1

    print("OK: import boundaries clean for", ", ".join(SCAN_DIRS))
    return 0


if __name__ == "__main__":
    sys.exit(main())
