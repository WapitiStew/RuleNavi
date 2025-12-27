# -*- coding: utf-8 -*-
##
# @file step2_p02_export_tree_json.py
# @brief Export rules tree (Type -> Major -> Sub -> Rule -> Chapter) as JSON for HTML left pane.
#
# @if japanese
# ## 目的（Step2-3 / No3）
# SQLite（rules DB）から分類・ルール・章（あれば）を取り出し、
# HTMLの左ペインで表示できるツリー構造のJSON（tree.json）を生成する。
#
# ### 出力（最小）
# - label : 表示名
# - path  : クリック時に開く先（ルールフォルダ/MDの基準となるパス）
# - children : 子ノード配列
#
# ### Done条件
# out/rules_tree/tree.json が生成される
# 後工程（HTML）がこのJSONだけで左ペインを描ける
# @endif
#
# @if english
# ## Goal (Step2-3 / No3)
# Export category/rule/chapter hierarchy from SQLite as a JSON tree (tree.json)
# that can directly render the HTML left pane.
#
# ### Output (minimum)
# - label : display name
# - path  : open target when clicked (base path to rule folder / MD)
# - children : child nodes
#
# ### Done
# out/rules_tree/tree.json is generated and HTML can render left pane only from this JSON.
# @endif
#
#

from __future__ import annotations

import argparse
import json
import logging
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

import setting_key as sk
import setting_helper as sh

# -----------------------------------------------------------------------------
# Imports for project utilities
# -----------------------------------------------------------------------------
try:
    import read_setting as rs  # type: ignore
except Exception:  # pragma: no cover
    import read_setting as rs  # type: ignore


# -----------------------------------------------------------------------------
# SQL helpers
# -----------------------------------------------------------------------------
def quote_ident(name: str) -> str:
    """Quote an SQLite identifier (table/column)."""
    return '"' + str(name).replace('"', '""') + '"'


def read_sql_df(conn: sqlite3.Connection, sql: str) -> pd.DataFrame:
    print(f"[Info] SQL: {sql}")
    return pd.read_sql_query(sql, conn)


# -----------------------------------------------------------------------------
# Tree builder
# -----------------------------------------------------------------------------
def ensure_child(parent: Dict[str, Any], key: str, label: str, path: str) -> Dict[str, Any]:
    if "_map" not in parent:
        parent["_map"] = {}

    m: Dict[str, Dict[str, Any]] = parent["_map"]
    if key in m:
        return m[key]

    node = {"label": label, "path": path.replace("\\", "/"), "children": []}
    m[key] = node
    parent["children"].append(node)
    return node


def finalize_tree(node: Dict[str, Any]) -> None:
    children = node.get("children", [])
    children.sort(key=lambda x: str(x.get("label", "")))
    for c in children:
        finalize_tree(c)

    node.pop("_map", None)


def pick_label(*candidates: Any) -> str:
    for c in candidates:
        if c is None:
            continue
        s = str(c).strip()
        if s and s.lower() != "nan":
            return s
    return "_"


def pick_segment(*candidates: Any) -> str:
    # folder-safe (最低限)
    s = pick_label(*candidates)
    for ch in ["\\", "/", ":", "*", "?", '"', "<", ">", "|", "\t", "\n", "\r"]:
        s = s.replace(ch, "_")
    s = s.rstrip(" .")
    return s if s else "_"


# -----------------------------------------------------------------------------
# Main logic (Step2-3)
# -----------------------------------------------------------------------------
def export_tree_json(*, out_path: Path) -> None:
    """!
    @if japanese
        @brief 分類＋ルール＋章（あれば）をツリーJSONとして書き出す。
    @endif
    @if english
        @brief Export category + rule + chapter (if any) as a JSON tree.
    @endif
    """
    logger = logging.getLogger(__name__)

    setting_csv = rs.load_setting_csv()

    # DBパス（Step2-2 と同じ解決）
    db_name = rs.get_setting_value(setting_csv, sk.KEY_DB_NAME)
    db_path = Path(sh.rules_file_fullpath(setting_csv, db_name))
    if not db_path.exists():
        raise FileNotFoundError(f"DB not found: {db_path}")

    # table names
    tbl_cat_type = rs.get_setting_value(setting_csv, sk.KEY_TBL_CAT_TYPE)
    tbl_cat_major = rs.get_setting_value(setting_csv, sk.KEY_TBL_CAT_MAJOR)
    tbl_cat_sub = rs.get_setting_value(setting_csv, sk.KEY_TBL_CAT_SUB)
    tbl_rules = rs.get_setting_value(setting_csv, sk.KEY_TBL_RULES)
    tbl_request = rs.get_setting_value(setting_csv, sk.KEY_TBL_REQUEST)

    # column names (category)
    col_type_pkey = rs.get_setting_value(setting_csv, sk.KEY_ITM_CAT_TYPE_PKEY)
    col_type_tjp = rs.get_setting_value(setting_csv, sk.KEY_ITM_CAT_TYPE_TITLE_JP)
    col_type_ten = rs.get_setting_value(setting_csv, sk.KEY_ITM_CAT_TYPE_TITLE_EN)
    col_type_path = rs.get_setting_value(setting_csv, sk.KEY_ITM_CAT_TYPE_PATH)

    col_major_pkey = rs.get_setting_value(setting_csv, sk.KEY_ITM_CAT_MAJOR_PKEY)
    col_major_tjp = rs.get_setting_value(setting_csv, sk.KEY_ITM_CAT_MAJOR_TITLE_JP)
    col_major_ten = rs.get_setting_value(setting_csv, sk.KEY_ITM_CAT_MAJOR_TITLE_EN)
    col_major_fkey = rs.get_setting_value(setting_csv, sk.KEY_ITM_CAT_MAJOR_FKEY_CAT_TYPE)
    col_major_path = rs.get_setting_value(setting_csv, sk.KEY_ITM_CAT_MAJOR_PATH)

    col_sub_pkey = rs.get_setting_value(setting_csv, sk.KEY_ITM_CAT_SUB_PKEY)
    col_sub_tjp = rs.get_setting_value(setting_csv, sk.KEY_ITM_CAT_SUB_TITLE_JP)
    col_sub_ten = rs.get_setting_value(setting_csv, sk.KEY_ITM_CAT_SUB_TITLE_EN)
    col_sub_fkey = rs.get_setting_value(setting_csv, sk.KEY_ITM_CAT_SUB_FKEY_CAT_MAJOR)
    col_sub_path = rs.get_setting_value(setting_csv, sk.KEY_ITM_CAT_SUB_PATH)

    # column names (rules)
    col_rule_pkey = rs.get_setting_value(setting_csv, sk.KEY_ITM_RULES_PKEY)
    col_rule_id = rs.get_setting_value(setting_csv, sk.KEY_ITM_RULES_ID_RULE)
    col_rule_name = rs.get_setting_value(setting_csv, sk.KEY_ITM_RULES_NAME_RULE)
    col_rule_fsub = rs.get_setting_value(setting_csv, sk.KEY_ITM_RULES_FKEY_CAT_SUB)

    # column names (request)
    col_req_key_rule = rs.get_setting_value(setting_csv, sk.KEY_ITM_REQUEST_KEY_RULE)
    col_req_id_cap = rs.get_setting_value(setting_csv, sk.KEY_ITM_REQUEST_ID_CAP)
    col_req_title_cap = rs.get_setting_value(setting_csv, sk.KEY_ITM_REQUEST_FTITLE_CAPTER)

    # SQL: Type->Major->Sub->Rule (+Chapter)
    sql = f"""
WITH caps AS (
  SELECT DISTINCT
    CAST({quote_ident(col_req_key_rule)} AS INTEGER) AS key_rule_int,
    {quote_ident(col_req_id_cap)} AS id_cap,
    {quote_ident(col_req_title_cap)} AS title_capter
  FROM {quote_ident(tbl_request)}
)
SELECT
  ct.{quote_ident(col_type_path)}  AS type_path,
  ct.{quote_ident(col_type_tjp)}   AS type_jp,
  ct.{quote_ident(col_type_ten)}   AS type_en,

  cm.{quote_ident(col_major_path)} AS major_path,
  cm.{quote_ident(col_major_tjp)}  AS major_jp,
  cm.{quote_ident(col_major_ten)}  AS major_en,

  cs.{quote_ident(col_sub_path)}   AS sub_path,
  cs.{quote_ident(col_sub_tjp)}    AS sub_jp,
  cs.{quote_ident(col_sub_ten)}    AS sub_en,

  r.{quote_ident(col_rule_pkey)}   AS key_rule,
  r.{quote_ident(col_rule_id)}     AS id_rule,
  r.{quote_ident(col_rule_name)}   AS name_rule,

  caps.id_cap,
  caps.title_capter
FROM {quote_ident(tbl_rules)} r
JOIN {quote_ident(tbl_cat_sub)} cs
  ON cs.{quote_ident(col_sub_pkey)} = r.{quote_ident(col_rule_fsub)}
JOIN {quote_ident(tbl_cat_major)} cm
  ON cm.{quote_ident(col_major_pkey)} = cs.{quote_ident(col_sub_fkey)}
JOIN {quote_ident(tbl_cat_type)} ct
  ON ct.{quote_ident(col_type_pkey)} = cm.{quote_ident(col_major_fkey)}
LEFT JOIN caps
  ON caps.key_rule_int = r.{quote_ident(col_rule_pkey)}
ORDER BY
  ct.{quote_ident(col_type_pkey)},
  cm.{quote_ident(col_major_pkey)},
  cs.{quote_ident(col_sub_pkey)},
  r.{quote_ident(col_rule_id)},
  caps.id_cap
"""
    with sqlite3.connect(db_path) as conn:
        df = read_sql_df(conn, sql)

    root: Dict[str, Any] = {"label": "__root__", "path": "", "children": []}

    # output base (rules dir under BUILD_DIR)
    rules_dir = rs.get_setting_value(setting_csv, sk.KEY_RULES_DIR)
    rules_file_dir = rs.get_setting_value(setting_csv, sk.KEY_RULES_FILE_DIR)
    prefix = (
        rules_dir
        if (rules_file_dir or "").strip() in ("", ".")
        else f"{rules_dir}/{rules_file_dir}"
    )

    for _, row in df.iterrows():
        type_seg = pick_segment(row["type_path"], row["type_en"])
        major_seg = pick_segment(row["major_path"], row["major_en"])
        sub_seg = pick_segment(row["sub_path"], row["sub_en"])
        rule_seg = pick_segment(row["id_rule"])
        cap_seg = pick_segment(row["id_cap"]) if pd.notna(row["id_cap"]) else ""

        type_label = pick_label(row["type_jp"], row["type_en"], type_seg)
        major_label = pick_label(row["major_jp"], row["major_en"], major_seg)
        sub_label = pick_label(row["sub_jp"], row["sub_en"], sub_seg)
        rule_label = pick_label(row["name_rule"], row["id_rule"])
        cap_label = pick_label(row["title_capter"], row["id_cap"]) if cap_seg else ""

        # path: rules/<type>/<major>/<sub>/<id_rule>/<id_cap?>
        type_path = f"{prefix}/{type_seg}"
        major_path = f"{prefix}/{type_seg}/{major_seg}"
        sub_path = f"{prefix}/{type_seg}/{major_seg}/{sub_seg}"
        rule_path = f"{prefix}/{type_seg}/{major_seg}/{sub_seg}/{rule_seg}"
        cap_path = f"{rule_path}/{cap_seg}" if cap_seg else rule_path

        n_type = ensure_child(root, f"type:{type_seg}", type_label, type_path)
        n_major = ensure_child(n_type, f"major:{major_seg}", major_label, major_path)
        n_sub = ensure_child(n_major, f"sub:{sub_seg}", sub_label, sub_path)
        n_rule = ensure_child(n_sub, f"rule:{rule_seg}", rule_label, rule_path)

        if cap_seg:
            ensure_child(n_rule, f"cap:{cap_seg}", cap_label, cap_path)

    finalize_tree(root)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(root["children"], ensure_ascii=False, indent=2), encoding="utf-8"
    )
    logger.info("Wrote: %s", out_path)


def main() -> int:
    """!
    @if japanese
        @brief CLIエントリポイント。
    @endif
    @if english
        @brief CLI entry point.
    @endif
    """
    parser = argparse.ArgumentParser(description="Step2-3: Export tree.json from SQLite.")
    parser.add_argument(
        "--out", type=str, default="", help="Output json path (default: out/rules_tree/tree.json)."
    )
    parser.add_argument(
        "--log-level", type=str, default="INFO", help="Logging level (DEBUG/INFO/WARNING/ERROR)."
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(levelname)s: %(message)s",
    )

    setting_csv = rs.load_setting_csv()
    json_tree_name = rs.get_setting_value(setting_csv, sk.KEY_JSON_MAIN_TREE)
    json_tree_fullpth = sh.json_file_fullpath(setting_csv, json_tree_name)

    default_out = Path(str(json_tree_fullpth))
    out_path = Path(args.out) if args.out else default_out

    print(f"Output JSON Path: {out_path}")
    export_tree_json(out_path=out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
