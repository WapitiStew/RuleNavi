# -*- coding: utf-8 -*-
##
# @file scripts/step1_p00_check_excel.py
# @brief Inspect configured Excel file and print sheet information for verification.
#
# @if japanese
# setting.csv からExcelの場所とファイル名を取得し、対象Excelのシート名と各シートの先頭5行を表示する確認用スクリプトです。
# 取り込み前に列構造やデータの有無を素早くチェックすることを目的にしています。
# 標準出力にのみ結果を出力し、ファイルやDBの変更は行いません。
# @endif
#
# @if english
# This helper script resolves the Excel path from setting.csv, lists sheet names, and prints the first five rows of each sheet.
# It is intended for quick structure checks before ingestion, emitting results to stdout only without modifying files or databases.
# @endif
#

import pandas as pd  # [JP] 外部: Excel読み込み用のデータ処理ライブラリ / [EN] External: Data handling for reading Excel files
from pathlib import Path  # [JP] 標準: パス操作ユーティリティ / [EN] Standard: path utilities

import read_setting as rs  # [JP] 自作: setting.csv の読込ユーティリティ / [EN] Local: utilities for loading setting.csv
import setting_key as sk  # [JP] 自作: 設定キー定数群 / [EN] Local: constants for setting keys


##
# @brief Entry point to inspect Excel sheets / Excelシートを確認するエントリーポイント
#
# @if japanese
# setting.csv からリソースディレクトリとExcelファイル名を取得し、対象Excelを開いてシート一覧を表示します。
# さらに各シートの先頭5行を表示して、列構造やサンプル値を目視確認できるようにします。
# @endif
#
# @if english
# Reads the resource directory and Excel filename from setting.csv, opens the Excel file, and prints its sheet list.
# Also prints the first five rows of each sheet to allow manual inspection of columns and sample values.
# @endif
#
def main():
    # [JP] 設定CSVからリソースディレクトリとExcelファイル名を取得 / [EN] Pull resource dir and Excel filename from setting CSV
    setting_csv = rs.load_setting_csv()
    resrc_dir = rs.get_setting_value(setting_csv, sk.KEY_RESRC_DIR)
    src_excel = rs.get_setting_value(setting_csv, sk.KEY_SRC_EXCEL)

    # [JP] Excelファイルへのフルパスを組み立て / [EN] Build full path to the Excel file
    EXCEL_PATH = Path(resrc_dir + "/" + src_excel)

    # [JP] シート一覧を取得して表示 / [EN] Enumerate sheet names and print them
    xls = pd.ExcelFile(EXCEL_PATH)
    print("Sheets:", xls.sheet_names)

    # [JP] 各シートの先頭5行を表示 / [EN] Print the head rows for each sheet
    for sheet_name in xls.sheet_names:
        df = pd.read_excel(EXCEL_PATH, sheet_name=sheet_name)
        print(f"=== {sheet_name} head ===")
        print(df.head())


if __name__ == "__main__":
    main()
