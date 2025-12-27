# -*- coding: utf-8 -*-
##
# @file src/read_setting.py
# @brief Helpers to load setting CSV files and parse schema definitions.
#
# @if japanese
# setting.csv や setting.col_subv を読み込み、キー値の取得やテーブル定義の抽出を行うユーティリティ関数群です。
# pandasが無い場合でもdict読み込みにフォールバックできるようにし、ファイル探索も安定するように工夫しています。
# スキーマ定義(ITM_*)を解析してCREATE TABLE用のカラム定義を返す機能も含みます。
# @endif
#
# @if english
# Utility functions to load setting.csv/setting.col_subv, retrieve values, and extract schema definitions.
# Provides fallbacks when pandas is unavailable and searches files upward for robustness.
# Also parses ITM_* rows to generate column definitions for CREATE TABLE statements.
# @endif
#

from __future__ import annotations

from pathlib import Path  # [JP] 標準: パス操作 / [EN] Standard: path utilities
from typing import Union, List, Dict, Tuple, Optional  # [JP] 標準: 型ヒント / [EN] Standard: type hints

try:
    import pandas as pd  # [JP] 外部: DataFrame処理 / [EN] External: DataFrame handling
except ImportError:
    pd = None


##
# @brief Search for a file upward from a starting directory / 開始ディレクトリから親方向にファイルを探索する
#
# @if japanese
# start_dir から順に親ディレクトリをたどり、最初に見つかったファイルパスを返します。見つからない場合は None を返します。
# @endif
#
# @if english
# Walks upward from start_dir through its parents, returning the first matching file path or None if not found.
# @endif
#
# @param filename [in]  探索するファイル名 / Filename to search for
# @param start_dir [in]  起点ディレクトリ / Starting directory
# @return Optional[Path]  見つかったPathまたはNone / Found path or None
def _find_file_upwards(filename: str, start_dir: Path) -> Optional[Path]:
    """
    start_dir から親方向に辿って filename を探す。
    見つかれば Path を返し、無ければ None。
    """
    cur = start_dir.resolve()
    for p in [cur, *cur.parents]:
        cand = p / filename
        if cand.exists():
            return cand.resolve()
    return None


##
# @brief Load a CSV into pandas DataFrame / CSVをpandasのDataFrameとして読み込む
#
# @if japanese
# 指定パスのCSVをpandasで読み込み、存在しない場合はFileNotFoundError、pandas未インストールならImportErrorを送出します。
# @endif
#
# @if english
# Reads the CSV at the given path using pandas, raising FileNotFoundError if missing or ImportError when pandas is unavailable.
# @endif
#
# @param csv_path [in]  CSVファイルパス / Path to the CSV file
# @param encoding [in]  テキストエンコーディング / Text encoding
# @return pd.DataFrame  読み込んだDataFrame / Loaded DataFrame
# @throws FileNotFoundError ファイルが存在しない場合 / When file does not exist
# @throws ImportError pandas未インストールの場合 / When pandas is not installed
def load_csv(csv_path: Union[str, Path], *, encoding: str = "utf-8-sig"):
    if pd is None:
        raise ImportError("pandas is not installed. Install it or use load_csv_as_dicts().")

    csv_path = Path(csv_path)
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV not found: {csv_path}")

    return pd.read_csv(csv_path, encoding=encoding)


##
# @brief Load setting CSV relative to current or module directory / カレントまたはモジュール基準でsetting.csvを読み込む
#
# @if japanese
# カレントディレクトリを優先し、なければread_setting.py基準、さらに親方向探索の順でsetting.csvを探します。
# 見つかったパスをpandasで読み込み、見つからない場合は試行候補を列挙した例外を送出します。
# @endif
#
# @if english
# Searches for setting.csv preferring current working dir, then module-relative path, then parent traversal.
# Loads the found file with pandas and raises an exception listing tried paths if not found.
# @endif
#
# @param filename [in]  ファイル名 (default: setting.csv) / Filename to search for
# @param data_dir [in]  モジュール基準の探索サブディレクトリ / Subdirectory relative to module base
# @param encoding [in]  テキストエンコーディング / Text encoding
# @return pd.DataFrame  読み込んだDataFrame / Loaded DataFrame
# @throws FileNotFoundError 探索失敗時 / When file is not found in any candidate
def load_setting_csv(
    *, filename: str = "setting.csv", data_dir: str = "..", encoding: str = "utf-8-sig"
):
    # [JP] 1) カレントディレクトリ直下を優先 / [EN] 1) Prefer current working directory
    cwd_candidate = Path.cwd() / filename
    if cwd_candidate.exists():
        return load_csv(cwd_candidate, encoding=encoding)

    # [JP] 2) モジュール基準の従来動作 / [EN] 2) Legacy behavior relative to module
    base_dir = Path(__file__).resolve().parent
    legacy_candidate = base_dir / data_dir / filename
    if legacy_candidate.exists():
        return load_csv(legacy_candidate, encoding=encoding)

    # [JP] 3) 親方向の探索でレイアウト変更にも対応 / [EN] 3) Search upwards to tolerate layout changes
    found = _find_file_upwards(filename, base_dir)
    if found is not None:
        return load_csv(found, encoding=encoding)

    # [JP] 4) 見つからなければ候補を列挙して例外 / [EN] 4) Raise with tried candidates
    raise FileNotFoundError(
        "CSV not found.\n"
        f"  tried:\n"
        f"    - {cwd_candidate}\n"
        f"    - {legacy_candidate}\n"
        f"    - upwards from: {base_dir}\n"
    )


##
# @brief Load CSV as list of dicts using stdlib / 標準ライブラリでCSVをdict配列として読み込む
#
# @if japanese
# pandas無しでも動作するよう、csv.DictReaderで読み込みます。値は文字列として扱われます。
# @endif
#
# @if english
# Reads CSV via csv.DictReader to work without pandas, treating all values as strings.
# @endif
#
# @param csv_path [in]  CSVファイルパス / Path to the CSV file
# @param encoding [in]  テキストエンコーディング / Text encoding
# @return List[Dict[str, str]]  行のリスト / List of row dictionaries
# @throws FileNotFoundError ファイルが存在しない場合 / When file does not exist
def load_csv_as_dicts(
    csv_path: Union[str, Path], *, encoding: str = "utf-8-sig"
) -> List[Dict[str, str]]:
    import csv  # [JP] 標準: CSV読み込み / [EN] Standard: CSV reader

    csv_path = Path(csv_path)
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV not found: {csv_path}")

    with csv_path.open("r", encoding=encoding, newline="") as f:
        return list(csv.DictReader(f))


##
# @brief Get value for a key from setting CSV / setting CSVからキー値を取得する
#
# @if japanese
# 先頭列をキーとしてindex化し、2列目の値を返します。DataFrameを変更せずに取得します。
# @endif
#
# @if english
# Indexes the first column as keys and returns the corresponding value from the second column.
# Leaves the original DataFrame unchanged.
# @endif
#
# @param csv [in]  読み込んだ設定DataFrame / Loaded settings DataFrame
# @param key [in]  取得するキー / Key to retrieve
# @return str  対応する値 / Retrieved value
def get_setting_value(csv: pd.DataFrame, key: str) -> str:
    setting_key = csv.set_index(csv.columns[0])
    setting_val = csv.columns[1]
    return setting_key.at[key, setting_val]


##
# @brief Get type for a key from setting CSV / setting CSVから型情報を取得する
#
# @if japanese
# 先頭列をキーとしてindex化し、3列目の型情報を返します。
# @endif
#
# @if english
# Indexes on the first column and returns the type information from the third column.
# @endif
#
# @param csv [in]  読み込んだ設定DataFrame / Loaded settings DataFrame
# @param key [in]  取得するキー / Key to retrieve
# @return str  型情報 / Type string
def get_setting_type(csv: pd.DataFrame, key: str) -> str:
    setting_key = csv.set_index(csv.columns[0])
    setting_type = csv.columns[2]
    return setting_key.at[key, setting_type]


##
# @brief Get remark for a key from setting CSV / setting CSVから備考を取得する
#
# @if japanese
# 先頭列をキーとしてindex化し、4列目の備考欄を返します。
# @endif
#
# @if english
# Indexes on the first column and returns the remark column (fourth column).
# @endif
#
# @param csv [in]  読み込んだ設定DataFrame / Loaded settings DataFrame
# @param key [in]  取得するキー / Key to retrieve
# @return str  備考文字列 / Remark string
def get_setting_remark(csv: pd.DataFrame, key: str) -> str:
    setting_key = csv.set_index(csv.columns[0])
    setting_remark = csv.columns[3]
    return setting_key.at[key, setting_remark]


##
# @brief Parse ITM_* rows into column definitions / ITM_* 行をカラム定義へ変換する
#
# @if japanese
# setting.csv の ITM_* 行を解析し、グループごとに(列名, 型, 備考)タプルのリストを返します。
# 型が空のときは key_ プレフィックスならINTEGER、それ以外はTEXTに自動補完します。
# @endif
#
# @if english
# Parses ITM_* rows from setting.csv and returns per-group lists of (column, type, remark).
# When type is empty, defaults to INTEGER for key_ prefixes, otherwise TEXT.
# @endif
#
# @param csv [in]  設定DataFrame / Settings DataFrame
# @param groups [in]  グループ名一覧 / List of group names
# @return Dict[str, List[Tuple[str, str, str]]]  グループごとの列定義 / Column definitions per group
# @throws ImportError pandas未インストール時 / If pandas is not installed
# @throws ValueError カラム定義不足や空名の場合 / If column definitions are missing or empty
def get_setting_sql_table_item(
    csv: pd.DataFrame, groups: List[str]
) -> Dict[str, List[Tuple[str, str, str]]]:
    """
    ITM_*** 行を解析し、グループごとの列定義を返す。
    戻り値は { "RULES": [(col, type, remark), ...], "CAT_TYPE": [...], ... }
    """
    if pd is None:
        raise ImportError("pandas is required for get_setting_sql_table_item().")

    result: Dict[str, List[Tuple[str, str, str]]] = {g: [] for g in groups}

    # [JP] ITM_* 行を走査しグループ別に追加 / [EN] Iterate ITM_* rows and bucket by group
    for _, row in csv.iterrows():
        k = str(row.get("key", "")).strip()
        if not k.startswith("ITM_"):
            continue

        # [JP] ITM_RULES_... / ITM_CAT_TYPE_... をグループ化 / [EN] Derive group name
        suffix = k[4:]  # remove "ITM_"
        parts = suffix.split("_")
        if len(parts) < 2:
            continue

        if parts[0] == "CAT":
            group = f"CAT_{parts[1]}"
        else:
            group = parts[0]

        if group not in result:
            continue

        col_name = "" if pd.isna(row.get("value")) else str(row.get("value")).strip()
        type_str = "" if pd.isna(row.get("type")) else str(row.get("type")).strip()
        remark = "" if pd.isna(row.get("remark")) else str(row.get("remark")).strip()

        if not col_name:
            raise ValueError(f"Column name is empty for key={k!r}")

        # [JP] 型が空ならkey_はINTEGER、それ以外はTEXT / [EN] Default types when missing
        if not type_str:
            type_str = "INTEGER" if col_name.startswith("key_") else "TEXT"

        result[group].append((col_name, type_str, remark))

    # [JP] 各グループに定義があるか検証 / [EN] Validate definitions exist for each group
    for g, cols in result.items():
        if len(cols) == 0:
            raise ValueError(
                f"No column definitions found for group {g}. (Expected ITM_{g}_... rows)"
            )

    return result


##
# @brief Load setting.col_subv as DataFrame / setting.col_subv をDataFrameで読み込む
#
# @if japanese
# setting.col_subv をCSVと同様の形式としてload_setting_csvを流用し読み込みます。
# @endif
#
# @if english
# Loads setting.col_subv treating it like a CSV by delegating to load_setting_csv.
# @endif
#
# @param filename [in]  ファイル名 / Filename
# @param data_dir [in]  基準ディレクトリ / Base directory relative to this module
# @param encoding [in]  エンコーディング / Encoding
# @return pd.DataFrame  読み込んだDataFrame / Loaded DataFrame
def load_setting_col_subv(
    *, filename: str = "setting.col_subv", data_dir: str = ".", encoding: str = "utf-8-sig"
):
    # [JP] CSVと同形式のため既存ローダーを再利用 / [EN] Reuse CSV loader due to identical format
    return load_setting_csv(filename=filename, data_dir=data_dir, encoding=encoding)
