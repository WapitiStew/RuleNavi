import sqlite3
from pathlib import Path
import pandas as pd

import read_setting as rs
import setting_key as sk
import setting_helper as sh


def quote_ident(name: str) -> str:
    """
    SQLite identifier quote.
    """
    # 最低限のエスケープ（ダブルクォートを2個にする）
    name = str(name).replace('"', '""')
    return f'"{name}"'


def main():
    setting_csv = rs.load_setting_csv()  # sub.py から見た data/sample.csv を読む
    db_name = rs.get_setting_value(setting_csv, sk.KEY_DB_NAME)
    DB_PATH = Path(sh.rules_file_fullpath(setting_csv, db_name))  # 作成される SQLite ファイル
    print(f"DB Path:    {DB_PATH}")
    print(setting_csv)

    if not DB_PATH.exists():
        print("DB not found:", DB_PATH)
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # テーブル一覧を表示
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';"
    )
    tables_in_db = {row[0] for row in cursor.fetchall()}
    print("Tables in DB:", sorted(tables_in_db))

    # CSVの key が TBL_ で始まる行を全部拾う
    tbl_rows = setting_csv[setting_csv["key"].astype(str).str.startswith("TBL_")].copy()
    tbl_rows["value"] = tbl_rows["value"].astype(str).str.strip()

    # NULLチェック.
    if tbl_rows.empty:
        print("No TBL_ entries found in setting CSV.")
        return

    # テーブルチェック.
    print("\n=== Check tables defined by TBL_* in CSV ===")
    for _, row in tbl_rows.iterrows():
        key = row["key"]
        tbl_name = row["value"]

        # KEY NULLチェック
        if not tbl_name or tbl_name.lower() == "nan":
            print(f"[NG] {key}: table name is empty")
            continue

        # VALUE NULLチェック
        if tbl_name not in tables_in_db:
            print(f"[NG] {key}: {tbl_name}  (NOT FOUND in DB)")
            continue

        # 行数
        cnt_df = pd.read_sql_query(f"SELECT COUNT(*) AS n FROM {quote_ident(tbl_name)};", conn)
        n = int(cnt_df.iloc[0]["n"])
        print(f"[OK] {key}: {tbl_name}  rows={n}")

        # サンプル表示（先頭20行）
        sample_df = pd.read_sql_query(f"SELECT * FROM {quote_ident(tbl_name)} LIMIT 20;", conn)
        print(sample_df)
        print("-" * 60)

    conn.close()


if __name__ == "__main__":
    main()
