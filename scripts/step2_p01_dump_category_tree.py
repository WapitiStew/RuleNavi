# -*- coding: utf-8 -*-
##
# @file step2_p01_dump_category_tree.py
# @brief Dump category tree (Type -> Major -> Sub) from SQLite as a text log.
#
# @if japanese
# ## 目的（Step2-2 / No2）
# SQLite（rules DB）に入っている分類テーブルから、
# 「大分類 > 中分類 > 小分類」のツリーをテキスト（ログ）として出力する。
#
# ## この版で直したこと
# - NameError（setting_col 未定義）を防ぐため、処理を main() 配下に統一
# - `setting.col_subv` は「実行時カレント(CWD)」を最優先で探索して読み込む
#   （read_setting.load_setting_col() は read_setting.py の場所基準で読むため、ズレやすい）
# - `DB_NAME` は setting.col_subv の値をそのまま優先しつつ、よくある配置も補助探索する
# @endif
#
# @if english
# ## Goal (Step2-2 / No2)
# Dump the category hierarchy (Type -> Major -> Sub) from SQLite into a human-readable text tree.
#
# ## Fixes in this version
# - Avoid NameError by keeping runtime logic inside main()
# - Load setting.col_subv from the current working directory first
# - Resolve DB_NAME from setting.col_subv, with extra fallback candidates
# @endif
#
#

from __future__ import annotations

import argparse
import logging
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import pandas as pd

import setting_key as sk
import setting_helper as sh


# -----------------------------------------------------------------------------
# Imports for project utilities
# -----------------------------------------------------------------------------
try:
    import utility.read_setting as rs  # type: ignore
except Exception:  # pragma: no cover
    import read_setting as rs  # type: ignore

import setting_key as sk


# -----------------------------------------------------------------------------
# DB path resolver (setting.col_subv DB_NAME first)
# -----------------------------------------------------------------------------
def resolve_db_path(setting_col: pd.DataFrame, setting_col_path: Path) -> Path:
    """!
    @if japanese
        @brief setting.col_subv の DB_NAME を読み取り、DBファイルのパスを解決する。
    @endif
    @if english
        @brief Resolve SQLite DB path from DB_NAME in setting.col_subv.
    @endif
    """    
    db_name = str(rs.get_setting_value(setting_col, sk.KEY_DB_NAME)).strip()
    raw = Path(db_name)

    base_dirs = [
        Path.cwd(),
        setting_col_path.parent,
        Path(__file__).resolve().parent,
    ]

    candidates: List[Path] = []

    for base in base_dirs:
        if raw.is_absolute():
            candidates.append(raw)
        else:
            candidates.append(base / raw)

        # common fallbacks
        candidates.extend([
            base / "rules" / "rule.db",
            base / "rules" / "rules.db",
            base / "rules.db",
            base / "rule.db",
        ])

    # de-dup
    seen: set[str] = set()
    uniq: List[Path] = []
    for p in candidates:
        key = str(p.resolve()) if p.exists() else str(p)
        if key in seen:
            continue
        seen.add(key)
        uniq.append(p)

    for p in uniq:
        if p.exists():
            return p

    tried = "\n".join(f"  - {p}" for p in uniq)
    raise FileNotFoundError(
        "SQLite DB not found.\n"
        f"setting.col_subv: {setting_col_path}\n"
        f"DB_NAME: {db_name}\n"
        "Tried:\n"
        f"{tried}\n"
        "\nHint: Fix DB_NAME in setting.col_subv (e.g. rules/rule.db)."
    )


# -----------------------------------------------------------------------------
# SQL helpers
# -----------------------------------------------------------------------------
def quote_ident(name: str) -> str:
    """Quote an SQLite identifier (table/column)."""
    return '"' + name.replace('"', '""') + '"'


def read_table_columns(
    conn: sqlite3.Connection,
    table_name: str,
    columns: Sequence[str],
    order_by: Optional[Sequence[str]] = None,
) -> pd.DataFrame:
    cols_sql = ", ".join(quote_ident(c) for c in columns)
    sql = f"SELECT {cols_sql} FROM {quote_ident(table_name)}"
    if order_by:
        ob_sql = ", ".join(quote_ident(c) for c in order_by)
        sql += f" ORDER BY {ob_sql}"

    print(f"[Info] SQL: {sql}")    
    return pd.read_sql_query(sql, conn)


def get_children(
        node_key: Tuple[str, Any],
        type_to_majors: Dict[Any, List[Tuple[str, Tuple[str, Any]]]],
        major_to_subs: Dict[Any, List[Tuple[str, Tuple[str, Any]]]]
) -> List[Tuple[str, Tuple[str, Any]]]:
    kind, key = node_key
    if kind == "type":
        return type_to_majors.get(key, [])
    if kind == "major":
        return major_to_subs.get(key, [])
    return []

# -----------------------------------------------------------------------------
# Tree rendering
# -----------------------------------------------------------------------------
def build_tree_lines(
    root_nodes: Sequence[Tuple[str, Tuple[str, Any]]],
    type_to_majors: Dict[Any, List[Tuple[str, Tuple[str, Any]]]],
    major_to_subs: Dict[Any, List[Tuple[str, Tuple[str, Any]]]]
) -> List[str]:
    lines: List[str] = []

    def walk(items: Sequence[Tuple[str, Tuple[str, Any]]], prefix: str) -> None:
        last_index = len(items) - 1
        for i, (label, node_key) in enumerate(items):
            is_last = (i == last_index)
            branch = "└ " if is_last else "├ "
            lines.append(prefix + branch + label)

            children = get_children(node_key, type_to_majors, major_to_subs)
            if children:
                extension = "  " if is_last else "│ "
                walk(children, prefix + extension)
    walk(root_nodes, "")
    return lines


# -----------------------------------------------------------------------------
# Main logic (Step2-2)
# -----------------------------------------------------------------------------
def dump_category_tree(*, out_path: Optional[Path]) -> None:
    """!
    @if japanese
        @brief 分類ツリー（大分類->中分類->小分類）をログ出力する。
    @endif
    @if english
        @brief Dump category tree (Type -> Major -> Sub) as a log text.
    @endif
    """    

    logger = logging.getLogger(__name__)

    setting_col= rs.load_setting_csv()

    # DBパス
    db_name   = rs.get_setting_value( setting_col, sk.KEY_DB_NAME )
    DB_PATH     = Path( sh.rules_file_fullpath( setting_col, db_name ) )   # 作成される SQLite ファイル
    if not DB_PATH.exists():
        print("DB not found:", DB_PATH)
        return

    # table names
    tbl_cat_type  = rs.get_setting_value(setting_col, sk.KEY_TBL_CAT_TYPE)
    tbl_cat_major = rs.get_setting_value(setting_col, sk.KEY_TBL_CAT_MAJOR)
    tbl_cat_sub   = rs.get_setting_value(setting_col, sk.KEY_TBL_CAT_SUB)
    print(f"[Info] TBL_CAME: {tbl_cat_type}")
    print(f"[Info] TBL_CAME: {tbl_cat_major}")
    print(f"[Info] TBL_CAME: {tbl_cat_sub}")

    # column names
    col_type_pkey  = rs.get_setting_value(setting_col, sk.KEY_ITM_CAT_TYPE_PKEY)
    col_type_title_jp   = rs.get_setting_value(setting_col, sk.KEY_ITM_CAT_TYPE_TITLE_JP)
    col_type_title_en   = rs.get_setting_value(setting_col, sk.KEY_ITM_CAT_TYPE_TITLE_EN)
    print(f"[Info] COLUMN: {tbl_cat_type} : {col_type_pkey}")
    print(f"[Info] COLUMN: {tbl_cat_type} : {col_type_title_jp}")
    print(f"[Info] COLUMN: {tbl_cat_type} : {col_type_title_en}")

    col_major_pkey      = rs.get_setting_value(setting_col, sk.KEY_ITM_CAT_MAJOR_PKEY)
    col_major_tjp       = rs.get_setting_value(setting_col, sk.KEY_ITM_CAT_MAJOR_TITLE_JP)
    col_major_ten       = rs.get_setting_value(setting_col, sk.KEY_ITM_CAT_MAJOR_TITLE_EN)
    col_major_fkey_type = rs.get_setting_value(setting_col, sk.KEY_ITM_CAT_MAJOR_FKEY_CAT_TYPE)
    print(f"[Info] COLUMN: {tbl_cat_major} : {col_major_pkey}")
    print(f"[Info] COLUMN: {tbl_cat_major} : {col_major_tjp}")
    print(f"[Info] COLUMN: {tbl_cat_major} : {col_major_fkey_type}")
    print(f"[Info] COLUMN: {tbl_cat_major} : {col_major_fkey_type}")

    col_sub_pkey       = rs.get_setting_value(setting_col, sk.KEY_ITM_CAT_SUB_PKEY)
    col_sub_tjp        = rs.get_setting_value(setting_col, sk.KEY_ITM_CAT_SUB_TITLE_JP)
    col_sub_ten        = rs.get_setting_value(setting_col, sk.KEY_ITM_CAT_SUB_TITLE_EN)
    col_sub_fkey_major = rs.get_setting_value(setting_col, sk.KEY_ITM_CAT_SUB_FKEY_CAT_MAJOR)
    print(f"[Info] COLUMN: {tbl_cat_sub} : {col_sub_pkey}")
    print(f"[Info] COLUMN: {tbl_cat_sub} : {col_sub_tjp}")
    print(f"[Info] COLUMN: {tbl_cat_sub} : {col_sub_ten}")
    print(f"[Info] COLUMN: {tbl_cat_sub} : {col_sub_fkey_major}")

    # query DB
    with sqlite3.connect(DB_PATH) as conn:
        type_df  = read_table_columns(conn, str(tbl_cat_type),  [col_type_pkey, col_type_title_jp, col_type_title_en], order_by=[col_type_pkey])
        major_df = read_table_columns(conn, str(tbl_cat_major), [col_major_pkey, col_major_tjp, col_major_ten, col_major_fkey_type], order_by=[col_major_fkey_type, col_major_pkey])
        sub_df   = read_table_columns(conn, str(tbl_cat_sub),   [col_sub_pkey, col_sub_tjp, col_sub_ten, col_sub_fkey_major], order_by=[col_sub_fkey_major, col_sub_pkey])

    # index
    # 中分類を「大分類ごと」にまとめる
    majors_by_type: Dict[Any, List[Dict[str, Any]]] = {}
    for _, row in major_df.iterrows():                                          #　中分類テーブルを確認
        majors_by_type.setdefault(row[col_major_fkey_type], []).append(row.to_dict())  #
    print(f"[Info] Dictionary: {majors_by_type}")

    # 小分類を「中分類ごと」にまとめる
    subs_by_major: Dict[Any, List[Dict[str, Any]]] = {}
    for _, row in sub_df.iterrows():
        subs_by_major.setdefault(row[col_sub_fkey_major], []).append(row.to_dict())
    print(f"[Info] Dictionary: {subs_by_major}")

    # labels
    def label_type(r: Dict[str, Any]) -> str:
        return f"[{r[col_type_pkey]}] {r.get(col_type_title_jp,'')} / {r.get(col_type_title_en,'')}"

    def label_major(r: Dict[str, Any]) -> str:
        return f"[{r[col_major_pkey]}] {r.get(col_major_tjp,'')} / {r.get(col_major_ten,'')}"

    def label_sub(r: Dict[str, Any]) -> str:
        return f"[{r[col_sub_pkey]}] {r.get(col_sub_tjp,'')} / {r.get(col_sub_ten,'')}"

    # tree nodes
    root_nodes: List[Tuple[str, Tuple[str, Any]]] = [
        (label_type(row.to_dict()), ("type", row[col_type_pkey])) for _, row in type_df.iterrows()
    ]

    type_to_majors: Dict[Any, List[Tuple[str, Tuple[str, Any]]]] = {}
    for tkey, items in majors_by_type.items():
        type_to_majors[tkey] = [(label_major(m), ("major", m[col_major_pkey])) for m in items]

    major_to_subs: Dict[Any, List[Tuple[str, Tuple[str, Any]]]] = {}
    for _, mrow in major_df.iterrows():
        mkey = mrow[col_major_pkey]
        items = subs_by_major.get(mkey, [])
        major_to_subs[mkey] = [(label_sub(s), ("sub", s[col_sub_pkey])) for s in items]

    lines = build_tree_lines(root_nodes, type_to_majors, major_to_subs)

    header = [
        "\n=== Category Tree Dump ===",
        f"DB: {DB_PATH}",
        "",
    ]
    text = "\n".join(header + lines) + "\n"
    print(text, end="")
    
    if out_path is not None:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(text, encoding="utf-8")
        logger.info("Wrote: %s", out_path)


def main() -> int:
    parser = argparse.ArgumentParser(description="Step2-2: Dump category tree from SQLite.")
    parser.add_argument("--out", type=str, default="", help="Output text path (default: stdout only).")
    parser.add_argument("--log-level", type=str, default="INFO", help="Logging level (DEBUG/INFO/WARNING/ERROR).")
    args = parser.parse_args()

    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO), format="%(levelname)s: %(message)s")

    out_path: Optional[Path] = Path(args.out) if args.out else None
    dump_category_tree(out_path=out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
