# -*- coding: utf-8 -*-
##
# @file scripts/step1_p01_import_excel_to_sqlite.py
# @brief Import Excel sheets into SQLite tables based on settings.
#
# @if japanese
# setting.csv で指定されたExcelファイルとスキーマ定義を読み込み、SQLite DBにテーブルを作成してデータを投入するスクリプトです。
# 各シートの先頭行をヘッダとし、不要な列を除去した上でINSERTします。開発・検証用に既存DBを削除して作り直します。
# ファイルパスやテーブル名は全て設定値から取得し、ログにSQLスクリプトを出力します。
# @endif
#
# @if english
# Script that reads the configured Excel file and schema definitions from setting.csv, creates SQLite tables, and inserts sheet data.
# Uses the first row as headers, prunes unused columns, and recreates the database from scratch for development/testing.
# All paths, table names, and column names are pulled from settings, and generated SQL scripts are logged.
# @endif
#

from pathlib import Path  # [JP] 標準: パス操作ユーティリティ / [EN] Standard: path utilities
from typing import List, Tuple  # [JP] 標準: 型ヒント（リスト・タプル） / [EN] Standard: type hints for lists/tuples
import sqlite3  # [JP] 標準: SQLite接続 / [EN] Standard: SQLite connectivity
import pandas as pd  # [JP] 外部: Excel読み込みとデータ整形 / [EN] External: Excel loading and data shaping
import re  # [JP] 標準: 正規表現による識別子検証 / [EN] Standard: regex for identifier validation

import read_setting as rs  # [JP] 自作: setting.csv 読み込みヘルパ / [EN] Local: helpers to load setting.csv
import setting_key as sk  # [JP] 自作: 設定キー定数群 / [EN] Local: constants for settings
import setting_helper as sh  # [JP] 自作: ルール関連パス補助 / [EN] Local: path helpers for rule resources


##
# @brief Load and clean an Excel sheet / Excelシートを読み込んで整形する
#
# @if japanese
# Excelファイルから指定シートをヘッダなしで読み込み、1行目をヘッダに採用します。
# 空の列や重複ヘッダを除去し、文字列列の前後空白をトリムして空文字や"nan"をNoneに置換します。
# SQLite挿入に適した整形済みDataFrameを返します。
# @endif
#
# @if english
# Reads a specific Excel sheet without headers, promotes the first row to header names,
# drops empty or duplicate columns, trims whitespace from string columns, and replaces empty/"nan" with None.
# Returns a cleaned DataFrame ready for SQLite insertion.
# @endif
#
# @param excel_path [in]  Excelファイルのパス / Path to the Excel file
# @param sheet_name [in]  読み込むシート名 / Target sheet name to read
# @return pd.DataFrame  整形済みのDataFrame / Cleaned DataFrame for insertion
def load_sheet_clean(excel_path: Path, sheet_name: str) -> pd.DataFrame:
    # [JP] シート情報をログ出力 / [EN] Log which Excel file and sheet are read
    print(f"Exxcel file: {excel_path}   /   Sheet: {sheet_name}")

    # [JP] ヘッダなしで生データを取得 / [EN] Load raw data without headers
    df_raw = pd.read_excel(excel_path, sheet_name=sheet_name, header=None)

    # [JP] 1行目をヘッダとして抽出 / [EN] Extract first row as header
    header = df_raw.iloc[0]
    df = df_raw.iloc[1:].copy()  # 2行目以降がデータ / data rows start at index 1
    df.columns = header  # [JP] ヘッダを列名に設定 / [EN] Apply header row as column names

    # [JP] NaNや空の列を除去 / [EN] Drop columns with NaN or empty headers
    df = df.loc[:, ~df.columns.isna()]

    # [JP] ヘッダ重複は最初の列のみ残す / [EN] Keep only the first occurrence of duplicated headers
    df = df.loc[:, ~df.columns.duplicated()]

    # [JP] 文字列列の前後空白を削除し空文字をNoneへ / [EN] Trim string columns and normalize blanks to None
    for col in df.columns:
        if df[col].dtype == object:
            df[col] = df[col].astype(str).str.strip()
            df[col] = df[col].replace({"": None, "nan": None})

    return df


##
# @brief Quote SQLite identifier safely / SQLiteの識別子を安全にクオートする
#
# @if japanese
# テーブル・カラム名が安全なパターンに合致するか検証し、ダブルクォートで囲んだ識別子文字列を返します。
# 許可されない文字が含まれる場合はValueErrorを送出します。
# @endif
#
# @if english
# Validates that a table/column name matches the allowed pattern and returns the double-quoted identifier string.
# Raises ValueError when disallowed characters are present.
# @endif
#
# @param name [in]  検証する識別子名 / Identifier name to validate
# @return str  ダブルクォート済み識別子 / Double-quoted identifier
# @throws ValueError 無効な識別子の場合 / If the identifier pattern is invalid
def quote_ident(name: str) -> str:
    # [JP] 許可パターンに合致するか正規表現で検証 / [EN] Validate identifier against regex pattern
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
        raise ValueError(f"Invalid table name: {name}")
    return f'"{name}"'  # SQLiteの識別子クォート / SQLite identifier quoting


##
# @brief Build CREATE TABLE SQL / CREATE TABLE文を組み立てる
#
# @if japanese
# 列定義のリストからCREATE TABLEスクリプトを生成します。列ごとにコメントを残し、識別子はquote_identで保護します。
# @endif
#
# @if english
# Generates a CREATE TABLE statement from column definitions, preserving remarks and quoting identifiers safely.
# @endif
#
# @param table_name [in]  作成するテーブル名 / Target table name to create
# @param col_defs [in]  (列名, 型, 備考)のリスト / List of (column, type, remark) tuples
# @return str  CREATE TABLE SQL文字列 / Generated CREATE TABLE SQL string
def build_create_table_sql(table_name: str, col_defs: List[Tuple[str, str, str]]) -> str:
    """列定義から CREATE TABLE 文を生成する。"""
    lines = []
    n = len(col_defs)

    for i, (col, typ, remark) in enumerate(col_defs):
        line = f"    {quote_ident(col)} {typ}"

        # [JP] カンマはコメントより前に付加 / [EN] Add comma before optional remark
        if i < n - 1:
            line += ","

        if remark and str(remark).strip() and str(remark).strip().lower() != "nan":
            r = str(remark).strip()
            # もし "--" が付いてなければ付ける（好みで） / prepend "--" to remarks if missing
            if not r.startswith("--"):
                r = "-- " + r
            line += f"  {r}"

        lines.append(line)

    body = "\n".join(lines)
    return f"CREATE TABLE {quote_ident(table_name)} (\n{body}\n);\n"


##
# @brief Create SQLite tables based on settings / 設定に基づきSQLiteテーブルを作成する
#
# @if japanese
# setting.csv からテーブル名と列定義を取得し、既存テーブルを削除した上でCREATE TABLEスクリプトを実行します。
# 主要テーブル（RULES, CAT_TYPE, CAT_MAJOR, CAT_SUB, CAT_STATE）の作成とコミットまで行います。
# @endif
#
# @if english
# Drops existing tables, builds CREATE TABLE scripts from setting.csv definitions, and executes them for core tables
# (RULES, CAT_TYPE, CAT_MAJOR, CAT_SUB, CAT_STATE), committing the schema setup.
# @endif
#
# @param csv [in]  設定CSV DataFrame / DataFrame for setting.csv
# @param conn [in]  SQLite接続オブジェクト / SQLite connection object
# @details
# @if japanese
# - 設定からテーブル名を収集しDROP文を生成して実行する。
# - グループごとの列定義を取得し、CREATE TABLE文を組み立てる。
# - 生成したDDLを実行しコミットする。
# @endif
# @if english
# - Collect table names from settings and run DROP statements.
# - Fetch column definitions per group and assemble CREATE TABLE statements.
# - Execute generated DDL and commit the schema changes.
# @endif
#
def create_tables(csv: pd.DataFrame, conn: sqlite3.Connection) -> None:
    cur = conn.cursor()

    # [JP] 設定から主要テーブル名を取得 / [EN] Fetch core table names from settings
    tbl_rules = rs.get_setting_value(csv, sk.KEY_TBL_RULES)
    tbl_cat_type = rs.get_setting_value(csv, sk.KEY_TBL_CAT_TYPE)
    tbl_cat_major = rs.get_setting_value(csv, sk.KEY_TBL_CAT_MAJOR)
    tbl_cat_sub = rs.get_setting_value(csv, sk.KEY_TBL_CAT_SUB)
    tbl_cat_state = rs.get_setting_value(csv, sk.KEY_TBL_CAT_STATE)

    table_names = {
        "RULES": tbl_rules,
        "CAT_TYPE": tbl_cat_type,
        "CAT_MAJOR": tbl_cat_major,
        "CAT_SUB": tbl_cat_sub,
        "CAT_STATE": tbl_cat_state,
    }

    # [JP] 既存テーブルをDROP / [EN] Drop existing tables before recreation
    drop_script = "\n".join(
        f"DROP TABLE IF EXISTS {quote_ident(name)};" for name in table_names.values()
    )
    print("SQL::DROP")
    print(drop_script)
    cur.executescript(drop_script)

    # [JP] 列定義をグループ単位で取得 / [EN] Fetch column definitions grouped by table
    groups = list(table_names.keys())
    item_defs = rs.get_setting_sql_table_item(csv, groups)

    # [JP] CREATE TABLEスクリプトを組み立て実行 / [EN] Build and run CREATE TABLE scripts
    create_script = ""
    for group, tbl_name in table_names.items():
        create_script += build_create_table_sql(tbl_name, item_defs[group])
    print("SQL::CREATE")
    print(create_script)
    cur.executescript(create_script)
    conn.commit()


##
# @brief Command entry to import Excel into SQLite / ExcelをSQLiteへ取り込むエントリーポイント
#
# @if japanese
# setting.csv を読み込み、DBパスを解決して既存DBを削除後、テーブル作成とデータ投入を行います。
# 各カテゴリ・ルール・リクエスト関連シートをロードし、設定で指定された列のみを残してto_sqlで挿入します。
# 実行結果とファイルパスを標準出力に表示し、完了時にDB生成を通知します。
# @endif
#
# @if english
# Loads settings, resolves the DB path, deletes any existing DB, creates tables, and inserts data from multiple Excel sheets.
# Each category/rule/request sheet is loaded, trimmed to configured columns, and inserted via to_sql.
# Paths and actions are printed to stdout, and a completion message indicates DB creation.
# @endif
#
# @details
# @if japanese
# - setting.csv を2回読み込み、ExcelパスとDBパスを決定する。
# - DB親フォルダの存在確認と作成、既存DB削除を行う。
# - create_tablesでDDLを実行後、各シートをロードし列を絞り込む。
# - pandasのto_sqlで各テーブルへデータをINSERTし、DBをクローズする。
# @endif
# @if english
# - Load setting.csv (twice) to resolve Excel and DB paths.
# - Validate/create DB parent directory and delete any existing DB file.
# - Run create_tables to set up schema, then load each sheet and trim columns.
# - Insert data into tables via pandas.to_sql and close the database connection.
# @endif
#
def main():
    # [JP] 設定CSVを読み込みExcel/DB情報を取得 / [EN] Load settings to resolve Excel/DB info
    setting_csv = rs.load_setting_csv()
    print(setting_csv)

    setting_csv = rs.load_setting_csv()
    src_excel = rs.get_setting_value(setting_csv, sk.KEY_SRC_EXCEL)
    db_name = rs.get_setting_value(setting_csv, sk.KEY_DB_NAME)

    # [JP] ExcelとDBのフルパスを解決 / [EN] Resolve full paths for Excel and DB
    EXCEL_PATH = Path(sh.resrc_file_fullpath(setting_csv, src_excel))  # Excel ファイル名（必要なら変更）
    DB_PATH = Path(sh.rules_file_fullpath(setting_csv, db_name))  # 作成されるSQLite ファイル
    print(f"Excel Path: {EXCEL_PATH}")
    print(f"DB Path:    {DB_PATH}")

    if not EXCEL_PATH.exists():
        print(f"Excel file not found: {EXCEL_PATH}")
        return

    # [JP] DB親パスの存在と種別を確認 / [EN] Ensure DB parent path exists and is a directory
    parent = DB_PATH.parent
    if parent.exists() and not parent.is_dir():
        raise RuntimeError(f"DB parent path exists but is not a directory: {parent}")

    # [JP] 親ディレクトリを必要に応じて作成 / [EN] Create parent directory if missing
    parent.mkdir(parents=True, exist_ok=True)

    # [JP] 既存DBを削除しリフレッシュ / [EN] Remove existing DB to rebuild from scratch
    if DB_PATH.exists():
        print(f"Delete DB file: {DB_PATH}")
        DB_PATH.unlink()

    # [JP] SQLite接続を確立 / [EN] Open SQLite connection
    sql_file = sqlite3.connect(DB_PATH)

    # [JP] スキーマ作成（カラム名・型を固定） / [EN] Create schema with fixed columns/types
    create_tables(setting_csv, sql_file)

    # [JP] 各シートを読み込み / [EN] Load sheets
    rules_df = load_sheet_clean(EXCEL_PATH, rs.get_setting_value(setting_csv, sk.KEY_TBL_RULES))
    cat_key_type_df = load_sheet_clean(
        EXCEL_PATH, rs.get_setting_value(setting_csv, sk.KEY_TBL_CAT_TYPE)
    )
    cat_major_df = load_sheet_clean(
        EXCEL_PATH, rs.get_setting_value(setting_csv, sk.KEY_TBL_CAT_MAJOR)
    )
    cat_sub_df = load_sheet_clean(EXCEL_PATH, rs.get_setting_value(setting_csv, sk.KEY_TBL_CAT_SUB))
    state_df = load_sheet_clean(EXCEL_PATH, rs.get_setting_value(setting_csv, sk.KEY_TBL_CAT_STATE))
    cat_request_df = load_sheet_clean(
        EXCEL_PATH, rs.get_setting_value(setting_csv, sk.KEY_TBL_CAT_REQUEST)
    )
    cat_phase_df = load_sheet_clean(
        EXCEL_PATH, rs.get_setting_value(setting_csv, sk.KEY_TBL_CAT_PHASE)
    )
    scp_sales_region_df = load_sheet_clean(
        EXCEL_PATH, rs.get_setting_value(setting_csv, sk.KEY_TBL_SCP_SALES_REGION)
    )
    scp_product_genre_df = load_sheet_clean(
        EXCEL_PATH, rs.get_setting_value(setting_csv, sk.KEY_TBL_SCP_PRODUCT_GENRE)
    )
    scp_service_genre_df = load_sheet_clean(
        EXCEL_PATH, rs.get_setting_value(setting_csv, sk.KEY_TBL_SCP_SERVICE_GENRE)
    )
    scp_equipment_df = load_sheet_clean(
        EXCEL_PATH, rs.get_setting_value(setting_csv, sk.KEY_TBL_SCP_EQUIPMENT)
    )
    scp_pii_df = load_sheet_clean(EXCEL_PATH, rs.get_setting_value(setting_csv, sk.KEY_TBL_SCP_PII))
    scp_design_domain_df = load_sheet_clean(
        EXCEL_PATH, rs.get_setting_value(setting_csv, sk.KEY_TBL_SCP_DESIGN_DOMAIN)
    )
    request_df = load_sheet_clean(EXCEL_PATH, rs.get_setting_value(setting_csv, sk.KEY_TBL_REQUEST))

    # --- 重要ポイント ------------------------------------------------------
    # [JP] DataFrameの列を存在する列に限定 / [EN] Restrict DataFrame columns to existing table columns
    rules_df = rules_df[
        [
            rs.get_setting_value(setting_csv, sk.KEY_ITM_RULES_PKEY),
            rs.get_setting_value(setting_csv, sk.KEY_ITM_RULES_ID_RULE),
            rs.get_setting_value(setting_csv, sk.KEY_ITM_RULES_NAME_RULE),
            rs.get_setting_value(setting_csv, sk.KEY_ITM_RULES_FKEY_CAT_SUB),
            rs.get_setting_value(setting_csv, sk.KEY_ITM_RULES_LINK),
            rs.get_setting_value(setting_csv, sk.KEY_ITM_RULES_FKEY_CAT_STATE),
            rs.get_setting_value(setting_csv, sk.KEY_ITM_RULES_CREATED_DATE),
            rs.get_setting_value(setting_csv, sk.KEY_ITM_RULES_UPDATE_DATE),
        ]
    ]

    cat_key_type_df = cat_key_type_df[
        [
            rs.get_setting_value(setting_csv, sk.KEY_ITM_CAT_TYPE_PKEY),
            rs.get_setting_value(setting_csv, sk.KEY_ITM_CAT_TYPE_TITLE_JP),
            rs.get_setting_value(setting_csv, sk.KEY_ITM_CAT_TYPE_TITLE_EN),
            rs.get_setting_value(setting_csv, sk.KEY_ITM_CAT_TYPE_PATH),
        ]
    ]

    cat_major_df = cat_major_df[
        [
            rs.get_setting_value(setting_csv, sk.KEY_ITM_CAT_MAJOR_PKEY),
            rs.get_setting_value(setting_csv, sk.KEY_ITM_CAT_MAJOR_TITLE_JP),
            rs.get_setting_value(setting_csv, sk.KEY_ITM_CAT_MAJOR_TITLE_EN),
            rs.get_setting_value(setting_csv, sk.KEY_ITM_CAT_MAJOR_FKEY_CAT_TYPE),
            rs.get_setting_value(setting_csv, sk.KEY_ITM_CAT_MAJOR_PATH),
        ]
    ]

    cat_sub_df = cat_sub_df[
        [
            rs.get_setting_value(setting_csv, sk.KEY_ITM_CAT_SUB_PKEY),
            rs.get_setting_value(setting_csv, sk.KEY_ITM_CAT_SUB_TITLE_JP),
            rs.get_setting_value(setting_csv, sk.KEY_ITM_CAT_SUB_TITLE_EN),
            rs.get_setting_value(setting_csv, sk.KEY_ITM_CAT_SUB_FKEY_CAT_MAJOR),
            rs.get_setting_value(setting_csv, sk.KEY_ITM_CAT_SUB_PATH),
        ]
    ]

    state_df = state_df[
        [
            rs.get_setting_value(setting_csv, sk.KEY_ITM_CAT_STATE_PKEY),
            rs.get_setting_value(setting_csv, sk.KEY_ITM_CAT_STATE_TITLE_JP),
            rs.get_setting_value(setting_csv, sk.KEY_ITM_CAT_STATE_TITLE_EN),
        ]
    ]

    cat_request_df = cat_request_df[
        [
            rs.get_setting_value(setting_csv, sk.KEY_ITM_CAT_REQUEST_PKEY),
            rs.get_setting_value(setting_csv, sk.KEY_ITM_CAT_REQUEST_TITLE_JP),
            rs.get_setting_value(setting_csv, sk.KEY_ITM_CAT_REQUEST_TITLE_EN),
            rs.get_setting_value(setting_csv, sk.KEY_ITM_CAT_REQUEST_KEY_CAT_REQ_TYPE),
            rs.get_setting_value(setting_csv, sk.KEY_ITM_CAT_REQUEST_REQ_TYPE),
        ]
    ]

    cat_phase_df = cat_phase_df[
        [
            rs.get_setting_value(setting_csv, sk.KEY_ITM_CAT_PHASE_PKEY),
            rs.get_setting_value(setting_csv, sk.KEY_ITM_CAT_PHASE_TITLE_JP),
            rs.get_setting_value(setting_csv, sk.KEY_ITM_CAT_PHASE_TITLE_EN),
        ]
    ]

    scp_sales_region_df = scp_sales_region_df[
        [
            rs.get_setting_value(setting_csv, sk.KEY_ITM_SCP_SALES_REGION_PKEY),
            rs.get_setting_value(setting_csv, sk.KEY_ITM_SCP_SALES_REGION_TITLE_JP),
            rs.get_setting_value(setting_csv, sk.KEY_ITM_SCP_SALES_REGION_TITLE_EN),
            rs.get_setting_value(setting_csv, sk.KEY_ITM_SCP_SALES_REGION_COUNTRY_CODE_2),
            rs.get_setting_value(setting_csv, sk.KEY_ITM_SCP_SALES_REGION_COUNTRY_CODE_3),
        ]
    ]

    scp_product_genre_df = scp_product_genre_df[
        [
            rs.get_setting_value(setting_csv, sk.KEY_ITM_SCP_PRODUCT_GENRE_PKEY),
            rs.get_setting_value(setting_csv, sk.KEY_ITM_SCP_PRODUCT_GENRE_TITLE_JP),
            rs.get_setting_value(setting_csv, sk.KEY_ITM_SCP_PRODUCT_GENRE_TITLE_EN),
            rs.get_setting_value(setting_csv, sk.KEY_ITM_SCP_PRODUCT_GENRE_HS_CODE),
        ]
    ]

    scp_service_genre_df = scp_service_genre_df[
        [
            rs.get_setting_value(setting_csv, sk.KEY_ITM_SCP_SERVICE_GENRE_PKEY),
            rs.get_setting_value(setting_csv, sk.KEY_ITM_SCP_SERVICE_GENRE_TITLE_JP),
            rs.get_setting_value(setting_csv, sk.KEY_ITM_SCP_SERVICE_GENRE_TITLE_EN),
        ]
    ]

    scp_equipment_df = scp_equipment_df[
        [
            rs.get_setting_value(setting_csv, sk.KEY_ITM_SCP_EQUIPMENT_PKEY),
            rs.get_setting_value(setting_csv, sk.KEY_ITM_SCP_EQUIPMENT_TITLE_JP),
            rs.get_setting_value(setting_csv, sk.KEY_ITM_SCP_EQUIPMENT_TITLE_EN),
        ]
    ]

    scp_pii_df = scp_pii_df[
        [
            rs.get_setting_value(setting_csv, sk.KEY_ITM_SCP_PII_PKEY),
            rs.get_setting_value(setting_csv, sk.KEY_ITM_SCP_PII_TITLE_JP),
            rs.get_setting_value(setting_csv, sk.KEY_ITM_SCP_PII_TITLE_EN),
        ]
    ]

    scp_design_domain_df = scp_design_domain_df[
        [
            rs.get_setting_value(setting_csv, sk.KEY_ITM_SCP_DESIGN_DOMAIN_PKEY),
            rs.get_setting_value(setting_csv, sk.KEY_ITM_SCP_DESIGN_DOMAIN_TITLE_JP),
            rs.get_setting_value(setting_csv, sk.KEY_ITM_SCP_DESIGN_DOMAIN_TITLE_EN),
        ]
    ]

    request_df = request_df[
        [
            rs.get_setting_value(setting_csv, sk.KEY_ITM_REQUEST_PKEY),
            rs.get_setting_value(setting_csv, sk.KEY_ITM_REQUEST_KEY_RULE),
            rs.get_setting_value(setting_csv, sk.KEY_ITM_REQUEST_ID_CAP),
            rs.get_setting_value(setting_csv, sk.KEY_ITM_REQUEST_FTITLE_CAPTER),
            rs.get_setting_value(setting_csv, sk.KEY_ITM_REQUEST_TITLE_SECTION),
            rs.get_setting_value(setting_csv, sk.KEY_ITM_REQUEST_FTOP_BODY),
            rs.get_setting_value(setting_csv, sk.KEY_ITM_REQUEST_LOW_BODY),
            rs.get_setting_value(setting_csv, sk.KEY_ITM_REQUEST_TOP_TBL),
            rs.get_setting_value(setting_csv, sk.KEY_ITM_REQUEST_TOP_FIG),
            rs.get_setting_value(setting_csv, sk.KEY_ITM_REQUEST_LOW_TBL),
            rs.get_setting_value(setting_csv, sk.KEY_ITM_REQUEST_LOW_FIG),
            rs.get_setting_value(setting_csv, sk.KEY_ITM_REQUEST_LEAD_TIME),
            rs.get_setting_value(setting_csv, sk.KEY_ITM_REQUEST_REFERENCE),
            rs.get_setting_value(setting_csv, sk.KEY_ITM_REQUEST_CREATED_DATE),
            rs.get_setting_value(setting_csv, sk.KEY_ITM_REQUEST_FUPDATE_DATE),
            rs.get_setting_value(setting_csv, sk.KEY_ITM_REQUEST_FKEY_CAT_REQUEST),
            rs.get_setting_value(setting_csv, sk.KEY_ITM_REQUEST_FKEY_CAT_PHASE),
            rs.get_setting_value(setting_csv, sk.KEY_ITM_REQUEST_FSCOPE_PRODUCT_GENRE),
            rs.get_setting_value(setting_csv, sk.KEY_ITM_REQUEST_FSCOPE_SERVICE_GENRE),
            rs.get_setting_value(setting_csv, sk.KEY_ITM_REQUEST_FSCOPE_EQUIPMENT),
            rs.get_setting_value(setting_csv, sk.KEY_ITM_REQUEST_FSCOPE_PII),
            rs.get_setting_value(setting_csv, sk.KEY_ITM_REQUEST_FSCOPE_DESIGN_DOMAIN),
            rs.get_setting_value(setting_csv, sk.KEY_ITM_REQUEST_UNIQUE_SEARCH),
        ]
    ]

    """
    """
    # [JP] DataFrameを既存テーブルにINSERT / [EN] Insert DataFrames into existing tables
    rules_df.to_sql(
        rs.get_setting_value(setting_csv, sk.KEY_TBL_RULES),
        sql_file,
        if_exists="append",
        index=False,
    )
    cat_key_type_df.to_sql(
        rs.get_setting_value(setting_csv, sk.KEY_TBL_CAT_TYPE),
        sql_file,
        if_exists="append",
        index=False,
    )
    cat_major_df.to_sql(
        rs.get_setting_value(setting_csv, sk.KEY_TBL_CAT_MAJOR),
        sql_file,
        if_exists="append",
        index=False,
    )
    cat_sub_df.to_sql(
        rs.get_setting_value(setting_csv, sk.KEY_TBL_CAT_SUB),
        sql_file,
        if_exists="append",
        index=False,
    )
    state_df.to_sql(
        rs.get_setting_value(setting_csv, sk.KEY_TBL_CAT_STATE),
        sql_file,
        if_exists="append",
        index=False,
    )
    cat_request_df.to_sql(
        rs.get_setting_value(setting_csv, sk.KEY_TBL_CAT_REQUEST),
        sql_file,
        if_exists="append",
        index=False,
    )
    cat_phase_df.to_sql(
        rs.get_setting_value(setting_csv, sk.KEY_TBL_CAT_PHASE),
        sql_file,
        if_exists="append",
        index=False,
    )
    scp_sales_region_df.to_sql(
        rs.get_setting_value(setting_csv, sk.KEY_TBL_SCP_SALES_REGION),
        sql_file,
        if_exists="append",
        index=False,
    )
    scp_product_genre_df.to_sql(
        rs.get_setting_value(setting_csv, sk.KEY_TBL_SCP_PRODUCT_GENRE),
        sql_file,
        if_exists="append",
        index=False,
    )
    scp_service_genre_df.to_sql(
        rs.get_setting_value(setting_csv, sk.KEY_TBL_SCP_SERVICE_GENRE),
        sql_file,
        if_exists="append",
        index=False,
    )
    scp_equipment_df.to_sql(
        rs.get_setting_value(setting_csv, sk.KEY_TBL_SCP_EQUIPMENT),
        sql_file,
        if_exists="append",
        index=False,
    )
    scp_pii_df.to_sql(
        rs.get_setting_value(setting_csv, sk.KEY_TBL_SCP_PII),
        sql_file,
        if_exists="append",
        index=False,
    )
    scp_design_domain_df.to_sql(
        rs.get_setting_value(setting_csv, sk.KEY_TBL_SCP_DESIGN_DOMAIN),
        sql_file,
        if_exists="append",
        index=False,
    )
    request_df.to_sql(
        rs.get_setting_value(setting_csv, sk.KEY_TBL_REQUEST),
        sql_file,
        if_exists="append",
        index=False,
    )

    sql_file.close()
    print("Done. SQLite DB created:", DB_PATH)


if __name__ == "__main__":
    main()
