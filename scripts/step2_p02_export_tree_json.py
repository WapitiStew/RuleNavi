# -*- coding: utf-8 -*-
##
# @file scripts/step2_p02_export_tree_json.py
# @brief Export rules tree (Type -> Major -> Sub -> Rule -> Chapter) as JSON for HTML navigation.
#
# @if japanese
# setting.csv で定義されたカテゴリ・ルール・章の情報をSQLiteから取得し、HTML左ペイン向けのツリーJSON(tree.json)を生成します。
# 出力はlabel/path/childrenを持つ構造で、後続の静的サイト生成でそのまま利用できます。
# DBパスや出力先は設定から解決し、必要に応じてコマンドライン引数で上書きできます。
# @endif
#
# @if english
# Generates tree.json for the HTML left pane by reading category/rule/chapter data from SQLite using setting.csv definitions.
# Produces a label/path/children structure consumable by later static site steps, resolving DB paths and output targets from settings.
# CLI arguments can override defaults without modifying underlying data or logic.
# @endif
#

from __future__ import annotations

import argparse  # [JP] 標準: CLI引数処理 / [EN] Standard: CLI argument parsing
import json  # [JP] 標準: JSONシリアライズ / [EN] Standard: JSON serialization
import logging  # [JP] 標準: ロギング / [EN] Standard: logging
import sqlite3  # [JP] 標準: SQLite接続 / [EN] Standard: SQLite connectivity
from pathlib import Path  # [JP] 標準: パス操作 / [EN] Standard: path utilities
from typing import Any, Dict, List, Optional  # [JP] 標準: 型ヒント / [EN] Standard: type hints

import pandas as pd  # [JP] 外部: DataFrame操作 / [EN] External: DataFrame handling

import setting_key as sk  # [JP] 自作: 設定キー定数 / [EN] Local: setting key constants
import setting_helper as sh  # [JP] 自作: パス解決ヘルパ / [EN] Local: path helpers

# -----------------------------------------------------------------------------
# Imports for project utilities
# -----------------------------------------------------------------------------
try:
    import read_setting as rs  # type: ignore  # [JP] 自作: 設定読込 / [EN] Local: load settings
except Exception:  # pragma: no cover
    import read_setting as rs  # type: ignore  # [JP] 自作: 設定読込フォールバック / [EN] Local: fallback loader


# -----------------------------------------------------------------------------
# SQL helpers
# -----------------------------------------------------------------------------
##
# @brief Quote SQLite identifier / SQLite識別子をクオートする
#
# @if japanese
# テーブル・カラム名に含まれるダブルクォートをエスケープし、SQLite用の識別子として括ります。
# @endif
#
# @if english
# Escapes embedded double quotes and wraps a table/column name for safe SQLite identifiers.
# @endif
#
# @param name [in]  識別子文字列 / Identifier string
# @return str  クオート済み文字列 / Quoted identifier string
def quote_ident(name: str) -> str:
    """Quote an SQLite identifier (table/column)."""
    return '"' + str(name).replace('"', '""') + '"'


##
# @brief Execute SQL and return DataFrame / SQLを実行してDataFrameを返す
#
# @if japanese
# SQLをログ出力し、結果をpandasのDataFrameとして返します。
# @endif
#
# @if english
# Logs the SQL statement and returns the result as a pandas DataFrame.
# @endif
#
# @param conn [in]  SQLite接続 / SQLite connection
# @param sql [in]  実行するSQL文字列 / SQL string to execute
# @return pd.DataFrame  実行結果 / Query result as DataFrame
def read_sql_df(conn: sqlite3.Connection, sql: str) -> pd.DataFrame:
    print(f"[Info] SQL: {sql}")
    return pd.read_sql_query(sql, conn)


# -----------------------------------------------------------------------------
# Tree builder
# -----------------------------------------------------------------------------
##
# @brief Ensure or create child node in tree / ツリー上の子ノードを取得または作成する
#
# @if japanese
# 親ノードの内部マップを用いてキーで子ノードを探索し、無ければlabel/path/childrenを持つ新規ノードを作成して返します。
# pathのバックスラッシュはスラッシュに正規化します。
# @endif
#
# @if english
# Uses the parent's internal map to fetch or create a child node keyed by the given value, normalizing path slashes.
# Returns the existing or newly created node with label/path/children fields.
# @endif
#
# @param parent [in]  親ノード辞書 / Parent node dictionary
# @param key [in]  子ノードの内部キー / Internal key for the child
# @param label [in]  表示ラベル / Display label
# @param path [in]  クリック時に開くパス / Path to open when clicked
# @return Dict[str, Any]  子ノード辞書 / Child node dictionary
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


##
# @brief Sort children and drop helper map / 子ノードの整列と補助マップの削除
#
# @if japanese
# childrenをlabel順にソートし、再帰的に子を処理した後、内部で使用した_mapを削除します。
# @endif
#
# @if english
# Sorts children by label, recurses into them, and removes the internal _map helper.
# @endif
#
# @param node [in]  ルートまたは中間ノード / Node to finalize
def finalize_tree(node: Dict[str, Any]) -> None:
    children = node.get("children", [])
    children.sort(key=lambda x: str(x.get("label", "")))
    for c in children:
        finalize_tree(c)

    node.pop("_map", None)


##
# @brief Pick display label from candidates / ラベル候補から優先的に選ぶ
#
# @if japanese
# Noneや空を除外し、最初に見つかった有効な文字列を返します。全て空なら"_"を返します。
# @endif
#
# @if english
# Returns the first non-empty/non-None candidate string; falls back to "_" if all are empty.
# @endif
#
# @param candidates [in]  ラベル候補 / Candidate values
# @return str  選択されたラベル / Chosen label
def pick_label(*candidates: Any) -> str:
    for c in candidates:
        if c is None:
            continue
        s = str(c).strip()
        if s and s.lower() != "nan":
            return s
    return "_"


##
# @brief Sanitize folder/path segment / フォルダ・パス用セグメントを安全化する
#
# @if japanese
# まずpick_labelで文字列を選び、禁止文字を"_"へ置換して末尾のスペース・ドットを除去します。
# 空の場合は"_"を返します。
# @endif
#
# @if english
# Selects a string via pick_label, replaces forbidden characters with "_", trims trailing spaces/dots, and returns "_" when empty.
# @endif
#
# @param candidates [in]  セグメント候補 / Segment candidates
# @return str  サニタイズ済みセグメント / Sanitized segment
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
##
# @brief Export category/rule/chapter tree to JSON / カテゴリ・ルール・章のツリーをJSON出力する
#
# @if japanese
# setting.csv からDBと各テーブル・カラム名を取得し、Type>Major>Sub>Rule>Chapterの階層をSQLで取得してJSON化します。
# rules_dirとrules_file_dirを結合してMDパスを形成し、pathにはスラッシュ区切りを用います。出力先はsetting.csvまたは--outで決定します。
# @endif
#
# @if english
# Pulls DB/table/column names from settings, queries Type>Major>Sub>Rule>Chapter hierarchy via SQL, and builds a JSON tree.
# Combines rules_dir and rules_file_dir to form MD paths, normalizing paths with slashes. Output path comes from settings or --out.
# @endif
#
# @param out_path [in]  出力JSONパス / Output JSON path
# @details
# @if japanese
# - DBパスを解決し存在確認する。
# - テーブル名とカラム名を設定から読み取る。
# - 階層取得のSQLを実行しDataFrame化する。
# - ツリー構造を構築し、label/path/children形式にまとめてソートする。
# - JSONを出力先へ書き出し、ログにパスを出力する。
# @endif
# @if english
# - Resolve and validate the DB path.
# - Read table and column names from settings.
# - Execute hierarchy SQL and load results into a DataFrame.
# - Build the tree structure with label/path/children and sort nodes.
# - Write JSON to the output path and log the location.
# @endif
#
def export_tree_json(*, out_path: Path) -> None:
    """!
    @if japanese
        @brief カテゴリ+ルール+章をツリーJSONとして出力します。
    @endif
    @if english
        @brief Export category + rule + chapter (if any) as a JSON tree.
    @endif
    """
    logger = logging.getLogger(__name__)

    # [JP] 設定読み込み / [EN] Load settings
    setting_csv = rs.load_setting_csv()

    # [JP] DBパスを解決 / [EN] Resolve DB path
    db_name = rs.get_setting_value(setting_csv, sk.KEY_DB_NAME)
    db_path = Path(sh.rules_file_fullpath(setting_csv, db_name))
    if not db_path.exists():
        raise FileNotFoundError(f"DB not found: {db_path}")

    # [JP] テーブル名 / [EN] Table names
    tbl_cat_type = rs.get_setting_value(setting_csv, sk.KEY_TBL_CAT_TYPE)
    tbl_cat_major = rs.get_setting_value(setting_csv, sk.KEY_TBL_CAT_MAJOR)
    tbl_cat_sub = rs.get_setting_value(setting_csv, sk.KEY_TBL_CAT_SUB)
    tbl_rules = rs.get_setting_value(setting_csv, sk.KEY_TBL_RULES)
    tbl_request = rs.get_setting_value(setting_csv, sk.KEY_TBL_REQUEST)

    # [JP] カラム名（カテゴリ） / [EN] Column names (category)
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

    # [JP] カラム名（ルール） / [EN] Column names (rules)
    col_rule_pkey = rs.get_setting_value(setting_csv, sk.KEY_ITM_RULES_PKEY)
    col_rule_id = rs.get_setting_value(setting_csv, sk.KEY_ITM_RULES_ID_RULE)
    col_rule_name = rs.get_setting_value(setting_csv, sk.KEY_ITM_RULES_NAME_RULE)
    col_rule_fsub = rs.get_setting_value(setting_csv, sk.KEY_ITM_RULES_FKEY_CAT_SUB)

    # [JP] カラム名（リクエスト/章） / [EN] Column names (request/chapter)
    col_req_key_rule = rs.get_setting_value(setting_csv, sk.KEY_ITM_REQUEST_KEY_RULE)
    col_req_id_cap = rs.get_setting_value(setting_csv, sk.KEY_ITM_REQUEST_ID_CAP)
    col_req_title_cap = rs.get_setting_value(setting_csv, sk.KEY_ITM_REQUEST_FTITLE_CAPTER)

    # [JP] 階層取得用SQL / [EN] SQL to fetch hierarchy
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
  r.{quote_ident(col_rule_id)}    ,
  caps.id_cap
"""
    with sqlite3.connect(db_path) as conn:
        df = read_sql_df(conn, sql)

    root: Dict[str, Any] = {"label": "__root__", "path": "", "children": []}

    # [JP] 出力用ベースパスを設定 / [EN] Set base path for output links
    rules_dir = rs.get_setting_value(setting_csv, sk.KEY_RULES_DIR)
    rules_file_dir = rs.get_setting_value(setting_csv, sk.KEY_RULES_FILE_DIR)
    prefix = (
        rules_dir
        if (rules_file_dir or "").strip() in ("", ".")
        else f"{rules_dir}/{rules_file_dir}"
    )

    # [JP] DataFrame行を走査しツリー構築 / [EN] Iterate rows to build tree
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

        # [JP] パス組み立て (rules/<type>/<major>/<sub>/<rule>/<cap?>) / [EN] Build hierarchical paths
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

    # [JP] JSON出力 / [EN] Write JSON output
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(root["children"], ensure_ascii=False, indent=2), encoding="utf-8"
    )
    logger.info("Wrote: %s", out_path)


##
# @brief CLI entry point / CLIエントリーポイント
#
# @if japanese
# --outと--log-levelを受け取り、設定からデフォルト出力先を解決してexport_tree_jsonを呼び出します。
# @endif
#
# @if english
# Parses --out and --log-level, resolves default output from settings, and calls export_tree_json.
# @endif
#
# @return int  終了コード / Exit code
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
