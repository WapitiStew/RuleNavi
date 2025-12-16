import pandas as pd
from pathlib import Path

import utility.read_setting as rs
import setting_key as sk

def main():

    setting_csv = rs.load_setting_csv()  # sub.py から見た data/sample.csv を読む
    EXCEL_PATH  = Path(rs.get_setting_value( setting_csv, sk.KEY_SRC_EXCEL ) )   # Excel ファイル名（必要なら変更）

    # Excel ファイルのシート一覧を表示
    xls = pd.ExcelFile(EXCEL_PATH)
    print("Sheets:", xls.sheet_names)

    # rules シートの先頭5行を表示（シート名が違う場合はここを変更）
    for sheet_name in xls.sheet_names:
        df = pd.read_excel(EXCEL_PATH, sheet_name=sheet_name)
        print(f"=== {sheet_name} head ===")
        print(df.head())

if __name__ == "__main__":
    main()
