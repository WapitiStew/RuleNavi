# -*- coding: utf-8 -*-
##
# @file src/sitegen/data.py
# @brief Data loading and Markdown-to-HTML conversion helpers for sitegen.
#
# @if japanese
# tree.jsonの読み込み、ノードの走査、Markdown(body.md)をHTMLに変換してbody.htmlを書き出す処理をまとめたモジュールです。
# ノード情報にhas_bodyフラグを付与し、tree_data.js用のJSを生成する機能も提供します。
# @endif
#
# @if english
# Provides helpers to load tree.json, traverse nodes, convert Markdown (body.md) to HTML, and write outputs for sitegen.
# Annotates nodes with has_body flags and generates tree_data.js for browser consumption.
# @endif
#

from __future__ import annotations

import json  # [JP] 標準: JSON読み書き / [EN] Standard: JSON handling
from pathlib import Path  # [JP] 標準: パス操作 / [EN] Standard: path utilities
from typing import Any, Dict, Iterable, List, Tuple  # [JP] 標準: 型ヒント / [EN] Standard: type hints

from sitegen.logger import Logger  # [JP] 自作: ログ出力 / [EN] Local: logger
from sitegen.md_html import md_to_html, wrap_body_html  # [JP] 自作: MD->HTML変換 / [EN] Local: Markdown conversion
from textio import read_text_auto, write_text_utf8  # [JP] 自作: エンコーディング統一I/O / [EN] Local: encoding-safe I/O helpers


##
# @brief Load tree.json as list / tree.jsonを読み込んでリストとして返す
#
# @if japanese
# 指定パスのtree.jsonをUTF-8で読み込み、ルートが配列であることを検証します。ログに読み込みパスを出力します。
# @endif
#
# @if english
# Reads tree.json from the given path (UTF-8), validates that the root is a list, and logs the read path.
# @endif
#
# @param path [in]  tree.jsonのパス / Path to tree.json
# @param log [in]  Loggerインスタンス / Logger instance
# @return List[Dict[str, Any]]  ツリーデータ配列 / Tree data list
# @throws ValueError ルートが配列でない場合 / If root is not a list
def load_tree_json(path: Path, log: Logger) -> List[Dict[str, Any]]:
    log.info(f"read: {path}")
    data = json.loads(read_text_auto(path))
    if not isinstance(data, list):
        raise ValueError("tree.json must be a JSON array at root.")
    return data


##
# @brief Iterate all nodes depth-first / 深さ優先でノードを走査するイテレータ
#
# @if japanese
# ツリーをスタックで管理し、children配列を持つノードを反転追加して深さ優先でyieldします。
# @endif
#
# @if english
# Traverses the tree depth-first using a stack, yielding each node; reverses children list to maintain order.
# @endif
#
# @param tree [in]  ツリー配列 / Tree list
# @return Iterable[Dict[str, Any]]  ノードイテレータ / Node iterator
def iter_nodes(tree: List[Dict[str, Any]]) -> Iterable[Dict[str, Any]]:
    stack = list(tree)
    while stack:
        n = stack.pop()
        yield n
        children = n.get("children") or []
        if isinstance(children, list):
            for c in reversed(children):
                stack.append(c)


##
# @brief Mark nodes with body presence and collect Markdown targets / 本文有無をマーキングしMarkdown対象を収集
#
# @if japanese
# 各ノードのpathからbody.mdの存在を確認し、has_bodyフラグを設定します。存在するものはtargetsに追加し、全ノード数とtargetsを返します。
# @endif
#
# @if english
# Checks for body.md under each node path, sets has_body flags, collects existing ones into targets, and returns total count with targets.
# @endif
#
# @param tree [in]  ツリーデータ / Tree data
# @param build_dir [in]  ビルドディレクトリ / Build directory
# @param md_name [in]  Markdownファイル名 / Markdown filename
# @param log [in]  Loggerインスタンス / Logger instance
# @return Tuple[int, List[Tuple[Dict[str, Any], Path]]]  (ノード総数, ターゲットリスト) / (total nodes, targets)
# @details
# @if japanese
# - pathが空の場合はhas_body=Falseにしてスキップ。
# - build_dir/path でdir_pathを作り、md_nameの存在を確認する。
# - 存在すればtargetsに(n, md_path)を追加し、ログにデバッグ情報を出す。
# @endif
# @if english
# - Skip empty path nodes (has_body=False).
# - Build dir_path via build_dir/path and check md_name existence.
# - Add (node, md_path) to targets when found and log debug info.
# @endif
#
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


##
# @brief Convert Markdown targets to body.html / Markdownターゲットをbody.htmlに変換する
#
# @if japanese
# 指定されたtarget一覧を走査し、body.mdを読み込んでHTML化し、同ディレクトリにbody.htmlを書き出します。
# 200件ごとに進捗ログを出力します。
# @endif
#
# @if english
# Iterates targets, reads body.md, converts to HTML, writes body.html in the same directory, and logs progress every 200 items.
# @endif
#
# @param targets [in]  (ノード, mdパス)リスト / List of (node, md path)
# @param log [in]  Loggerインスタンス / Logger instance
def convert_md_targets_to_html(
    targets: List[Tuple[Dict[str, Any], Path]],
    log: Logger,
) -> None:
    total = len(targets)
    for i, (node, md_path) in enumerate(targets, 1):
        label = str(node.get("label") or "")
        rel_dir = str(node.get("path") or "")
        log.debug(f"convert[{i}/{total}]: {label} ({rel_dir}) -> {md_path}")

        md_text = read_text_auto(md_path)

        body = md_to_html(md_text)
        title = label if label else md_path.parent.name
        html_text = wrap_body_html(body, title=title)

        out_html = md_path.parent / "body.html"
        write_text_utf8(out_html, html_text)

        if i % 200 == 0:
            log.info(f"converted: {i}/{total}")


##
# @brief Write tree data JS for browser / ブラウザ用tree_data.jsを書き出す
#
# @if japanese
# tree配列をJSON化し、window.RULENAVI_TREE に代入するJSとしてdataディレクトリへ保存します。file://アクセスを想定したシンプルな形式です。
# @endif
#
# @if english
# Serializes the tree list and writes it as window.RULENAVI_TREE assignment in data/tree_data.js, suitable for file:// usage.
# @endif
#
# @param out_dir [in]  dataディレクトリパス / Output directory
# @param tree [in]  ツリーデータ / Tree data
# @param log [in]  Loggerインスタンス / Logger instance
def write_tree_data_js(out_dir: Path, tree: List[Dict[str, Any]], log: Logger) -> None:
    out_path = out_dir / "tree_data.js"
    payload = json.dumps(tree, ensure_ascii=False)
    js = "// Auto-generated (file:// friendly)\nwindow.RULENAVI_TREE = " + payload + ";\n"
    write_text_utf8(out_path, js)
    log.info(f"write: {out_path}")
