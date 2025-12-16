import sqlite3
from pathlib import Path
import pandas as pd

import utility.read_setting as rs
import setting_key as sk

def quote_ident(name: str) -> str:
    """
    SQLite identifier quote.
    """
    # 最低限のエスケープ（ダブルクォートを2個にする）
    name = str(name).replace('"', '""')
    return f'"{name}"'


def main():
    setting_csv = rs.load_setting_csv()  # sub.py から見た data/sample.csv を読む
    print(setting_csv)
    DB_PATH     = Path( rs.get_setting_value( setting_csv, sk.KEY_DB_NAME ) )              # 作成される SQLite ファイル

    if not DB_PATH.exists():
        print("DB not found:", DB_PATH)
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # テーブル一覧を表示
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
    tables_in_db = {row[0] for row in cursor.fetchall()}
    print("Tables in DB:", sorted(tables_in_db))

    conn.close()
    
if __name__ == "__main__":
    main()
