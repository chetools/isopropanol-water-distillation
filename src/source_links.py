"""Stable GitHub links to the exact lines implementing named Python symbols."""

import ast
from pathlib import Path


REPOSITORY_URL = "https://github.com/chetools/isopropanol-water-distillation"


def github_symbol_link(label: str, relative_path: str, symbol: str) -> str:
    """Return Markdown linking a label to the current source lines for symbol."""
    repo_root = Path(__file__).resolve().parent.parent
    source = (repo_root / relative_path).read_text(encoding="utf-8")
    name = symbol.rsplit(".", 1)[-1]
    matches = [
        node
        for node in ast.walk(ast.parse(source))
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
        and node.name == name
    ]
    if not matches:
        return ""
    node = matches[0]
    start, end = node.lineno, node.end_lineno or node.lineno
    url = f"{REPOSITORY_URL}/blob/main/{relative_path}#L{start}-L{end}"
    return f"[**{label}** — `{relative_path}` lines {start}–{end}]({url})"
