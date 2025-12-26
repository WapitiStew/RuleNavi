# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

from sitegen.logger import Logger
from sitegen.md_html import md_to_html, wrap_body_html


def load_tree_json(path: Path, log: Logger) -> List[Dict[str, Any]]:
    log.info(f"read: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("tree.json must be a JSON array at root.")
    return data


def iter_nodes(tree: List[Dict[str, Any]]) -> Iterable[Dict[str, Any]]:
    stack = list(tree)
    while stack:
        n = stack.pop()
        yield n
        children = n.get("children") or []
        if isinstance(children, list):
            for c in reversed(children):
                stack.append(c)


def mark_and_collect_md_targets(
    tree: List[Dict[str, Any]],
    build_dir: Path,
    md_name: str,
    log: Logger,
) -> Tuple[int, List[Tuple[Dict[str, Any], Path]]]:
    targets: List[Tuple[Dict[str, Any], Path]] = []
    count = 0

    for n in iter_nodes(tree):
        count += 1
        rel = str(n.get("path") or "").strip()
        if rel == "":
            n["has_body"] = False
            continue

        dir_path = (build_dir / Path(rel)).resolve()
        md_path = dir_path / md_name
        log.debug(f"scan: path='{rel}' -> md='{md_path}'")

        if md_path.exists() and md_path.is_file():
            n["has_body"] = True
            targets.append((n, md_path))
        else:
            n["has_body"] = False

    return count, targets


def convert_md_targets_to_html(
    targets: List[Tuple[Dict[str, Any], Path]],
    log: Logger,
) -> None:
    total = len(targets)
    for i, (node, md_path) in enumerate(targets, 1):
        label = str(node.get("label") or "")
        rel_dir = str(node.get("path") or "")
        log.debug(f"convert[{i}/{total}]: {label} ({rel_dir}) -> {md_path}")

        try:
            md_text = md_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            md_text = md_path.read_text(encoding="cp932")

        body = md_to_html(md_text)
        title = label if label else md_path.parent.name
        html_text = wrap_body_html(body, title=title)

        out_html = md_path.parent / "body.html"
        out_html.write_text(html_text, encoding="utf-8")

        if i % 200 == 0:
            log.info(f"converted: {i}/{total}")


def write_tree_data_js(out_dir: Path, tree: List[Dict[str, Any]], log: Logger) -> None:
    out_path = out_dir / "tree_data.js"
    payload = json.dumps(tree, ensure_ascii=False)
    js = (
        "// Auto-generated (file:// friendly)\n"
        "window.RULENAVI_TREE = "
        + payload
        + ";\n"
    )
    out_path.write_text(js, encoding="utf-8")
    log.info(f"write: {out_path}")
