# -*- coding: utf-8 -*-
##
# @file scripts/step1_p02_check_db.py
# @brief Validate SQLite DB tables against setting.csv definitions.
#
# @if japanese
# setting.csv で定義されたテーブル名（TBL_*）がSQLite DBに存在するか確認し、件数とサンプル行を表示するチェックスクリプトです。
# DBパスは設定から解決し、テーブルごとにレコード数と先頭サンプルを標準出力へ出力します。
# 不足テーブルや空値を検出し、簡易的な品質チェックに利用します。
# @endif
#
# @if english
# Checker script that verifies whether tables defined by setting.csv (TBL_*) exist in the SQLite DB, printing counts and samples.
# Resolves the DB path from settings, outputs row counts and sample data for each table to stdout.
# Reports missing tables or empty values to support quick quality validation.
# @endif
#

import sqlite3  # [JP] 標準: SQLite接続 / [EN] Standard: SQLite connectivity
from pathlib import Path  # [JP] 標準: パス操作ユーティリティ / [EN] Standard: path utilities
import pandas as pd  # [JP] 外部: SQL結果のDataFrame処理 / [EN] External: DataFrame handling for SQL results

import read_setting as rs  # [JP] 自作: 設定CSV読込 / [EN] Local: load setting.csv
import setting_key as sk  # [JP] 自作: 設定キー定数 / [EN] Local: setting key constants
import setting_helper as sh  # [JP] 自作: パス解決ヘルパ / [EN] Local: helpers for resolving paths


##
# @brief Quote SQLite identifier / SQLite識別子をクオートする
#
# @if japanese
# テーブル名やカラム名に含まれるダブルクォートをエスケープし、SQLite識別子として安全に括ります。
# @endif
#
# @if english
# Escapes embedded double quotes and wraps the value for safe use as an SQLite identifier.
# @endif
#
# @param name [in]  識別子文字列 / Identifier string
# @return str  クオート済み識別子 / Quoted identifier string
def quote_ident(name: str) -> str:
    """
    SQLite identifier quote.
    """
    # [JP] ダブルクォートをエスケープ / [EN] Escape embedded double quotes
    name = str(name).replace('"', '""')
    return f'"{name}"'


##
# @brief Main entry to check DB tables / DBテーブルを確認するエントリーポイント
#
# @if japanese
# setting.csv からDBパスとTBL_*エントリを取得し、DB内テーブル一覧と突き合わせます。
# 行数を取得した上で先頭20件を表示し、欠損や未定義のテーブルを検出します。
# @endif
#
# @if english
# Loads DB path and TBL_* entries from setting.csv, compares them with the actual tables in SQLite, and prints row counts.
# Shows the first 20 rows for each existing table while flagging missing definitions or empty names.
# @endif
#
# @details
# @if japanese
# - setting.csv を読み込みDBパスを解決する。
# - DBが存在しない場合はエラーを表示して終了する。
# - sqlite_masterからユーザー定義テーブル一覧を取得する。
# - setting.csv でTBL_プレフィクスの行を抽出し、名前の空判定と存在チェックを行う。
# - 存在するテーブルは件数とサンプル行を表示する。
# @endif
# @if english
# - Load setting.csv and resolve the DB path.
# - Exit early if the DB file is missing.
# - Query sqlite_master for user tables.
# - Extract rows with TBL_ prefix from settings, validate non-empty names, and check existence.
# - For existing tables, print row counts and sample rows.
# @endif
#
def main():
    # [JP] 設定CSVからDBパスを取得 / [EN] Resolve DB path from settings
    setting_csv = rs.load_setting_csv()
    db_name = rs.get_setting_value(setting_csv, sk.KEY_DB_NAME)
    DB_PATH = Path(sh.rules_file_fullpath(setting_csv, db_name))  # 生成されたSQLite ファイル
    print(f"DB Path:    {DB_PATH}")
    print(setting_csv)

    if not DB_PATH.exists():
        print("DB not found:", DB_PATH)
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # [JP] DB内のユーザーテーブル一覧を取得 / [EN] Fetch user tables from sqlite_master
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';"
    )
    tables_in_db = {row[0] for row in cursor.fetchall()}
    print("Tables in DB:", sorted(tables_in_db))

    # [JP] 設定CSVからTBL_*行を抽出 / [EN] Extract TBL_* rows from settings
    tbl_rows = setting_csv[setting_csv["key"].astype(str).str.startswith("TBL_")].copy()
    tbl_rows["value"] = tbl_rows["value"].astype(str).str.strip()

    # [JP] 定義が無ければ早期終了 / [EN] Exit if no TBL_* entries are found
    if tbl_rows.empty:
        print("No TBL_ entries found in setting CSV.")
        return

    # [JP] TBL_*定義を順に確認 / [EN] Validate each TBL_* definition
    print("\n=== Check tables defined by TBL_* in CSV ===")
    for _, row in tbl_rows.iterrows():
        key = row["key"]
        tbl_name = row["value"]

        # [JP] テーブル名が空ならNG / [EN] Flag empty table names
        if not tbl_name or tbl_name.lower() == "nan":
            print(f"[NG] {key}: table name is empty")
            continue

        # [JP] DB未存在ならNG / [EN] Flag missing tables in DB
        if tbl_name not in tables_in_db:
            print(f"[NG] {key}: {tbl_name}  (NOT FOUND in DB)")
            continue

        # [JP] 件数を取得 / [EN] Fetch row count
        cnt_df = pd.read_sql_query(f"SELECT COUNT(*) AS n FROM {quote_ident(tbl_name)};", conn)
        n = int(cnt_df.iloc[0]["n"])
        print(f"[OK] {key}: {tbl_name}  rows={n}")

        # [JP] 先頭20件を表示して形を確認 / [EN] Show top 20 rows to inspect shape
        sample_df = pd.read_sql_query(f"SELECT * FROM {quote_ident(tbl_name)} LIMIT 20;", conn)
        print(sample_df)
        print("-" * 60)

    conn.close()


if __name__ == "__main__":
    main()
