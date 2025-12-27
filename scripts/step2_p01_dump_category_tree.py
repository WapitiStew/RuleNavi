# -*- coding: utf-8 -*-
##
# @file scripts/step2_p01_dump_category_tree.py
# @brief Dump category hierarchy (Type -> Major -> Sub) from SQLite as text.
#
# @if japanese
# setting.csv で定義されたカテゴリテーブルをSQLiteから取得し、階層構造をテキストツリーとして出力します。
# 標準出力への表示に加え、--out指定があればファイルにも書き出します。DBパスやテーブル・カラム名は設定から解決します。
# フォルダやDBを変更せず、内容確認用のダンプのみを行います。
# @endif
#
# @if english
# Loads category tables defined in setting.csv from SQLite and renders the hierarchy as a text tree.
# Prints to stdout and optionally writes to a file via --out. Table and column names as well as DB path are resolved from settings.
# Does not modify folders or the database; it purely produces a dump for inspection.
# @endif
#

from __future__ import annotations

import argparse  # [JP] 標準: コマンドライン引数処理 / [EN] Standard: CLI argument handling
import logging  # [JP] 標準: ロギング設定 / [EN] Standard: logging utilities
import sqlite3  # [JP] 標準: SQLite接続 / [EN] Standard: SQLite connectivity
from pathlib import Path  # [JP] 標準: パス操作 / [EN] Standard: path utilities
from typing import Any, Dict, List, Optional, Sequence, Tuple  # [JP] 標準: 型ヒント / [EN] Standard: type hints

import pandas as pd  # [JP] 外部: DataFrame操作 / [EN] External: DataFrame handling

import setting_key as sk  # [JP] 自作: 設定キー定数 / [EN] Local: setting key constants
import setting_helper as sh  # [JP] 自作: パス解決ヘルパ / [EN] Local: helpers for path resolution


# -----------------------------------------------------------------------------
# Imports for project utilities
# -----------------------------------------------------------------------------
try:
    import utility.read_setting as rs  # type: ignore  # [JP] 自作: 設定読込（utility配下） / [EN] Local utility: load settings
except Exception:  # pragma: no cover
    import read_setting as rs  # type: ignore  # [JP] 自作: 設定読込（通常パス） / [EN] Local: fallback settings loader

import setting_key as sk  # [JP] 自作: 設定キー定数（再インポート保持） / [EN] Local: setting keys (kept as in original)


# -----------------------------------------------------------------------------
# DB path resolver (setting.col_subv DB_NAME first)
# -----------------------------------------------------------------------------
##
# @brief Resolve DB path from setting.col_subv / setting.col_subv からDBパスを解決する
#
# @if japanese
# setting.col_subv の DB_NAME を基点に、現在ディレクトリや設定ファイルの親ディレクトリなど複数候補を組み合わせて存在確認します。
# 最初に存在するパスを返し、見つからない場合は試行した全候補を含む例外を送出します。
# @endif
#
# @if english
# Resolves the SQLite DB path using DB_NAME from setting.col_subv, combining current dir and config parent as base candidates.
# Returns the first existing path found; raises an exception listing all tried candidates if none exist.
# @endif
#
# @param setting_col [in]  setting.col_subvのDataFrame / DataFrame of setting.col_subv
# @param setting_col_path [in]  setting.col_subvのパス / Path to setting.col_subv
# @return Path  解決されたDBパス / Resolved DB path
# @throws FileNotFoundError DBが見つからない場合 / When no DB candidate exists
def resolve_db_path(setting_col: pd.DataFrame, setting_col_path: Path) -> Path:
    """!
    @if japanese
        @brief setting.col_subv の DB_NAME からSQLite DBのフルパスを導きます。
    @endif
    @if english
        @brief Resolve SQLite DB path from DB_NAME in setting.col_subv.
    @endif
    """
    db_name = str(rs.get_setting_value(setting_col, sk.KEY_DB_NAME)).strip()
    raw = Path(db_name)

    # [JP] 探索ベースとなるディレクトリ候補 / [EN] Base directories to probe
    base_dirs = [
        Path.cwd(),
        setting_col_path.parent,
        Path(__file__).resolve().parent,
    ]

    candidates: List[Path] = []

    # [JP] 絶対/相対の双方で候補を生成し共通フォールバックも追加 / [EN] Generate absolute/relative candidates plus common fallbacks
    for base in base_dirs:
        if raw.is_absolute():
            candidates.append(raw)
        else:
            candidates.append(base / raw)

        candidates.extend(
            [
                base / "rules" / "rule.db",
                base / "rules" / "rules.db",
                base / "rules.db",
                base / "rule.db",
            ]
        )

    # [JP] 重複候補を除去 / [EN] De-duplicate candidates
    seen: set[str] = set()
    uniq: List[Path] = []
    for p in candidates:
        key = str(p.resolve()) if p.exists() else str(p)
        if key in seen:
            continue
        seen.add(key)
        uniq.append(p)

    # [JP] 存在する最初の候補を返す / [EN] Return the first existing candidate
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
##
# @brief Quote an SQLite identifier / SQLite識別子をクオートする
#
# @if japanese
# カラムやテーブル名に含まれるダブルクォートをエスケープし、SQLite用の識別子として括ります。
# @endif
#
# @if english
# Escapes embedded double quotes and wraps the value for safe SQLite identifiers.
# @endif
#
# @param name [in]  識別子文字列 / Identifier string
# @return str  クオート済み文字列 / Quoted string
def quote_ident(name: str) -> str:
    """Quote an SQLite identifier (table/column)."""
    return '"' + name.replace('"', '""') + '"'


##
# @brief Read specific columns from a table / テーブルから指定カラムを取得する
#
# @if japanese
# SELECTクエリを生成し、必要に応じてORDER BY句を付けてDataFrameで返します。SQLは標準出力へログ出力します。
# @endif
#
# @if english
# Builds a SELECT statement for chosen columns, optionally with ORDER BY, logs the SQL, and returns the result as a DataFrame.
# @endif
#
# @param conn [in]  SQLite接続 / SQLite connection
# @param table_name [in]  テーブル名 / Table name
# @param columns [in]  取得するカラム名シーケンス / Sequence of column names
# @param order_by [in]  並び替えカラム（任意） / Optional ordering columns
# @return pd.DataFrame  取得結果のDataFrame / Resulting DataFrame
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


##
# @brief Get children nodes for tree / ツリーノードの子を取得する
#
# @if japanese
# ノード種別(type/major)に応じて、対応する子リストを辞書から取り出し返します。
# @endif
#
# @if english
# Returns child node entries based on the node kind (type/major) using prepared mapping dictionaries.
# @endif
#
# @param node_key [in]  ("type" or "major", キー) / Tuple of kind and key
# @param type_to_majors [in]  type -> majors 対応辞書 / Mapping of type to majors
# @param major_to_subs [in]  major -> subs 対応辞書 / Mapping of major to subs
# @return List[Tuple[str, Tuple[str, Any]]]  子ノードリスト / Child node list
def get_children(
    node_key: Tuple[str, Any],
    type_to_majors: Dict[Any, List[Tuple[str, Tuple[str, Any]]]],
    major_to_subs: Dict[Any, List[Tuple[str, Tuple[str, Any]]]],
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
##
# @brief Build tree lines for display / ツリー表示用の文字列を生成する
#
# @if japanese
# ルートノードと子ノード辞書をたどって、接続線付きの行リストを作成します。子はラベル順を維持しつつ深さ優先で処理します。
# @endif
#
# @if english
# Walks root nodes using mapping dictionaries to produce lines with branch markers, traversing children depth-first while preserving order.
# @endif
#
# @param root_nodes [in]  ルートノードのリスト / List of root nodes
# @param type_to_majors [in]  type -> majors 辞書 / Mapping of type to majors
# @param major_to_subs [in]  major -> subs 辞書 / Mapping of major to subs
# @return List[str]  ツリー行リスト / List of tree-rendered lines
def build_tree_lines(
    root_nodes: Sequence[Tuple[str, Tuple[str, Any]]],
    type_to_majors: Dict[Any, List[Tuple[str, Tuple[str, Any]]]],
    major_to_subs: Dict[Any, List[Tuple[str, Tuple[str, Any]]]],
) -> List[str]:
    lines: List[str] = []

    # [JP] 再帰的に木をたどり描画 / [EN] Recursively walk the tree to render lines
    def walk(items: Sequence[Tuple[str, Tuple[str, Any]]], prefix: str) -> None:
        last_index = len(items) - 1
        for i, (label, node_key) in enumerate(items):
            is_last = i == last_index
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
##
# @brief Dump category tree as text / カテゴリツリーをテキストとしてダンプする
#
# @if japanese
# setting.csv からDBやテーブル・カラム名を取得し、Type/Major/Subの3階層をSQLで読み出して文字列ツリーにします。
# 標準出力に結果を表示し、--out指定があればファイルにも保存します。DB未存在時は処理を中断します。
# @endif
#
# @if english
# Retrieves DB/table/column names from settings, loads Type/Major/Sub hierarchy from SQLite, and renders it as a text tree.
# Prints to stdout and optionally writes to a file when --out is specified; stops early if the DB is missing.
# @endif
#
# @param out_path [in]  出力テキストパス（任意） / Optional output text path
# @details
# @if japanese
# - setting.csv を読み込みDBパスを解決する。
# - テーブル名とカラム名を設定から取得し、各テーブルをDataFrameとして読み込む。
# - Type -> Major -> Subの対応辞書を構築し、ラベル文字列を組み立てる。
# - ツリー行を生成し標準出力へ表示、指定があればファイルへ書き出す。
# @endif
# @if english
# - Load setting.csv and resolve the DB path.
# - Acquire table and column names from settings and read each table into DataFrames.
# - Build mappings for Type -> Major -> Sub and generate label strings.
# - Render tree lines, print to stdout, and optionally write to a file.
# @endif
#
def dump_category_tree(*, out_path: Optional[Path]) -> None:
    """!
    @if japanese
        @brief カテゴリ(Type>Major>Sub)をツリー文字列として出力します。
    @endif
    @if english
        @brief Dump category tree (Type -> Major -> Sub) as a log text.
    @endif
    """

    logger = logging.getLogger(__name__)

    # [JP] 設定CSV読み込み / [EN] Load setting CSV
    setting_col = rs.load_setting_csv()

    # [JP] DBパス解決 / [EN] Resolve DB path
    db_name = rs.get_setting_value(setting_col, sk.KEY_DB_NAME)
    DB_PATH = Path(sh.rules_file_fullpath(setting_col, db_name))  # 作成される SQLite ファイル
    if not DB_PATH.exists():
        print("DB not found:", DB_PATH)
        return

    # [JP] テーブル名の取得 / [EN] Fetch table names
    tbl_cat_type = rs.get_setting_value(setting_col, sk.KEY_TBL_CAT_TYPE)
    tbl_cat_major = rs.get_setting_value(setting_col, sk.KEY_TBL_CAT_MAJOR)
    tbl_cat_sub = rs.get_setting_value(setting_col, sk.KEY_TBL_CAT_SUB)
    print(f"[Info] TBL_CAME: {tbl_cat_type}")
    print(f"[Info] TBL_CAME: {tbl_cat_major}")
    print(f"[Info] TBL_CAME: {tbl_cat_sub}")

    # [JP] カラム名の取得 / [EN] Fetch column names
    col_type_pkey = rs.get_setting_value(setting_col, sk.KEY_ITM_CAT_TYPE_PKEY)
    col_type_title_jp = rs.get_setting_value(setting_col, sk.KEY_ITM_CAT_TYPE_TITLE_JP)
    col_type_title_en = rs.get_setting_value(setting_col, sk.KEY_ITM_CAT_TYPE_TITLE_EN)
    print(f"[Info] COLUMN: {tbl_cat_type} : {col_type_pkey}")
    print(f"[Info] COLUMN: {tbl_cat_type} : {col_type_title_jp}")
    print(f"[Info] COLUMN: {tbl_cat_type} : {col_type_title_en}")

    col_major_pkey = rs.get_setting_value(setting_col, sk.KEY_ITM_CAT_MAJOR_PKEY)
    col_major_tjp = rs.get_setting_value(setting_col, sk.KEY_ITM_CAT_MAJOR_TITLE_JP)
    col_major_ten = rs.get_setting_value(setting_col, sk.KEY_ITM_CAT_MAJOR_TITLE_EN)
    col_major_fkey_type = rs.get_setting_value(setting_col, sk.KEY_ITM_CAT_MAJOR_FKEY_CAT_TYPE)
    print(f"[Info] COLUMN: {tbl_cat_major} : {col_major_pkey}")
    print(f"[Info] COLUMN: {tbl_cat_major} : {col_major_tjp}")
    print(f"[Info] COLUMN: {tbl_cat_major} : {col_major_fkey_type}")
    print(f"[Info] COLUMN: {tbl_cat_major} : {col_major_fkey_type}")

    col_sub_pkey = rs.get_setting_value(setting_col, sk.KEY_ITM_CAT_SUB_PKEY)
    col_sub_tjp = rs.get_setting_value(setting_col, sk.KEY_ITM_CAT_SUB_TITLE_JP)
    col_sub_ten = rs.get_setting_value(setting_col, sk.KEY_ITM_CAT_SUB_TITLE_EN)
    col_sub_fkey_major = rs.get_setting_value(setting_col, sk.KEY_ITM_CAT_SUB_FKEY_CAT_MAJOR)
    print(f"[Info] COLUMN: {tbl_cat_sub} : {col_sub_pkey}")
    print(f"[Info] COLUMN: {tbl_cat_sub} : {col_sub_tjp}")
    print(f"[Info] COLUMN: {tbl_cat_sub} : {col_sub_ten}")
    print(f"[Info] COLUMN: {tbl_cat_sub} : {col_sub_fkey_major}")

    # [JP] DBから各テーブルを取得 / [EN] Query DB for each table
    with sqlite3.connect(DB_PATH) as conn:
        type_df = read_table_columns(
            conn,
            str(tbl_cat_type),
            [col_type_pkey, col_type_title_jp, col_type_title_en],
            order_by=[col_type_pkey],
        )
        major_df = read_table_columns(
            conn,
            str(tbl_cat_major),
            [col_major_pkey, col_major_tjp, col_major_ten, col_major_fkey_type],
            order_by=[col_major_fkey_type, col_major_pkey],
        )
        sub_df = read_table_columns(
            conn,
            str(tbl_cat_sub),
            [col_sub_pkey, col_sub_tjp, col_sub_ten, col_sub_fkey_major],
            order_by=[col_sub_fkey_major, col_sub_pkey],
        )

    # [JP] Type->Major 辞書の構築 / [EN] Build mapping from type to majors
    majors_by_type: Dict[Any, List[Dict[str, Any]]] = {}
    for _, row in major_df.iterrows():
        majors_by_type.setdefault(row[col_major_fkey_type], []).append(row.to_dict())
    print(f"[Info] Dictionary: {majors_by_type}")

    # [JP] Major->Sub 辞書の構築 / [EN] Build mapping from major to subs
    subs_by_major: Dict[Any, List[Dict[str, Any]]] = {}
    for _, row in sub_df.iterrows():
        subs_by_major.setdefault(row[col_sub_fkey_major], []).append(row.to_dict())
    print(f"[Info] Dictionary: {subs_by_major}")

    # [JP] ラベル生成関数 / [EN] Label builders
    def label_type(r: Dict[str, Any]) -> str:
        return (
            f"[{r[col_type_pkey]}] {r.get(col_type_title_jp, '')} / {r.get(col_type_title_en, '')}"
        )

    def label_major(r: Dict[str, Any]) -> str:
        return f"[{r[col_major_pkey]}] {r.get(col_major_tjp, '')} / {r.get(col_major_ten, '')}"

    def label_sub(r: Dict[str, Any]) -> str:
        return f"[{r[col_sub_pkey]}] {r.get(col_sub_tjp, '')} / {r.get(col_sub_ten, '')}"

    # [JP] ルートノード(Type)作成 / [EN] Build root nodes for types
    root_nodes: List[Tuple[str, Tuple[str, Any]]] = [
        (label_type(row.to_dict()), ("type", row[col_type_pkey])) for _, row in type_df.iterrows()
    ]

    # [JP] Type -> Major のノード対応 / [EN] Map types to major node tuples
    type_to_majors: Dict[Any, List[Tuple[str, Tuple[str, Any]]]] = {}
    for tkey, items in majors_by_type.items():
        type_to_majors[tkey] = [(label_major(m), ("major", m[col_major_pkey])) for m in items]

    # [JP] Major -> Sub のノード対応 / [EN] Map majors to sub node tuples
    major_to_subs: Dict[Any, List[Tuple[str, Tuple[str, Any]]]] = {}
    for _, mrow in major_df.iterrows():
        mkey = mrow[col_major_pkey]
        items = subs_by_major.get(mkey, [])
        major_to_subs[mkey] = [(label_sub(s), ("sub", s[col_sub_pkey])) for s in items]

    # [JP] ツリー文字列の組み立て / [EN] Build tree lines
    lines = build_tree_lines(root_nodes, type_to_majors, major_to_subs)

    header = [
        "\n=== Category Tree Dump ===",
        f"DB: {DB_PATH}",
        "",
    ]
    text = "\n".join(header + lines) + "\n"
    print(text, end="")

    # [JP] ファイル出力（任意） / [EN] Optional file output
    if out_path is not None:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(text, encoding="utf-8")
        logger.info("Wrote: %s", out_path)


##
# @brief CLI entry point / CLIエントリーポイント
#
# @if japanese
# コマンドライン引数から出力先とログレベルを受け取り、dump_category_treeを呼び出します。
# @endif
#
# @if english
# Parses CLI arguments for output path and log level, then invokes dump_category_tree.
# @endif
#
# @return int  終了コード / Exit code
def main() -> int:
    parser = argparse.ArgumentParser(description="Step2-2: Dump category tree from SQLite.")
    parser.add_argument(
        "--out", type=str, default="", help="Output text path (default: stdout only)."
    )
    parser.add_argument(
        "--log-level", type=str, default="INFO", help="Logging level (DEBUG/INFO/WARNING/ERROR)."
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(levelname)s: %(message)s",
    )

    out_path: Optional[Path] = Path(args.out) if args.out else None
    dump_category_tree(out_path=out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
