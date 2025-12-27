# -*- coding: utf-8 -*-
"""!
@file sub.py
@brief \jp CSV読み込みユーティリティ \en CSV loader utilities
@details \jp CSVファイルを読み込む補助関数群。 \en Helper functions to load CSV files.
"""

from __future__ import annotations

from pathlib import Path
from typing import Union, List, Dict, Tuple, Optional

try:
    import pandas as pd
except ImportError:
    pd = None


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
# @brief \jp CSVをpandasのDataFrameとして読み込む \en Load a CSV into a pandas DataFrame
# @details \jp 指定されたCSVを読み込みDataFrameを返す。 \en Reads the CSV and returns a DataFrame.
# @param csv_path \jp 読み込むCSVへのパス \en Path to the CSV file to load
# @param encoding \jp 文字エンコーディング（例: "utf-8-sig", "cp932"） \en Text encoding (e.g., "utf-8-sig", "cp932")
# @return \jp 読み込んだ表データ（DataFrame） \en Loaded tabular data (DataFrame)
# @throws FileNotFoundError \jp 指定ファイルが存在しない場合 \en If the file does not exist
# @throws ImportError \jp pandasがインストールされていない場合 \en If pandas is not installed
##
def load_csv(csv_path: Union[str, Path], *, encoding: str = "utf-8-sig"):
    if pd is None:
        raise ImportError("pandas is not installed. Install it or use load_csv_as_dicts().")

    csv_path = Path(csv_path)
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV not found: {csv_path}")

    return pd.read_csv(csv_path, encoding=encoding)


##
# @brief \jp sub.py基準でdata配下のCSVを読み込む \en Load a CSV under data/ relative to sub.py
# @details \jp 実行時のカレントディレクトリに依存しない。 \en Independent from the current working directory.
# @param filename \jp 読み込むファイル名 \en CSV file name
# @param data_dir \jp dataフォルダ名 \en Data directory name
# @param encoding \jp 文字エンコーディング \en Text encoding
# @return \jp 読み込んだ表データ（DataFrame） \en Loaded tabular data (DataFrame)
# @throws FileNotFoundError \jp 指定ファイルが存在しない場合 \en If the file does not exist
# @throws ImportError \jp pandasがインストールされていない場合 \en If pandas is not installed
##
def load_setting_csv(
    *, filename: str = "setting.csv", data_dir: str = "..", encoding: str = "utf-8-sig"
):
    # 1) まずはカレント（RuleNavi直下想定）を優先する
    #    tools\*.bat が cd .. して ROOT に移動してから実行するため、ここで安定して拾える
    cwd_candidate = Path.cwd() / filename
    if cwd_candidate.exists():
        return load_csv(cwd_candidate, encoding=encoding)

    # 2) 従来の動作：read_setting.py 基準で相対パス解決
    base_dir = Path(__file__).resolve().parent
    legacy_candidate = base_dir / data_dir / filename
    if legacy_candidate.exists():
        return load_csv(legacy_candidate, encoding=encoding)

    # 3) レイアウト変更（src/scripts分離）でも拾えるよう、親方向へ探索
    found = _find_file_upwards(filename, base_dir)
    if found is not None:
        return load_csv(found, encoding=encoding)

    # 4) 最後にエラー（候補を明示）
    raise FileNotFoundError(
        "CSV not found.\n"
        f"  tried:\n"
        f"    - {cwd_candidate}\n"
        f"    - {legacy_candidate}\n"
        f"    - upwards from: {base_dir}\n"
    )


##
# @brief \jp 標準ライブラリでCSVをdict配列として読み込む \en Load a CSV as list[dict] using stdlib
# @details \jp pandas無しでも動く。値は全て文字列。 \en Works without pandas. Values are read as strings.
# @param csv_path \jp 読み込むCSVへのパス \en Path to the CSV file to load
# @param encoding \jp 文字エンコーディング \en Text encoding
# @return \jp 行データ配列（列名→値のdict） \en List of rows (dict: column -> value)
# @throws FileNotFoundError \jp 指定ファイルが存在しない場合 \en If the file does not exist
##
def load_csv_as_dicts(
    csv_path: Union[str, Path], *, encoding: str = "utf-8-sig"
) -> List[Dict[str, str]]:
    import csv

    csv_path = Path(csv_path)
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV not found: {csv_path}")

    with csv_path.open("r", encoding=encoding, newline="") as f:
        return list(csv.DictReader(f))


##
# @brief \jp CSVから特定キーの値を取得する \en Get a specific key's value from a CSV
# @return \jp キーに対応する値 \en Value corresponding to the key
# @param csv \jp 読み込んだCSVデータ（DataFrame） \en Loaded CSV data (DataFrame)
# @param key \jp 取得したいキー \en Key to retrieve
##
def get_setting_value(csv: pd.DataFrame, key: str) -> str:
    setting_key = csv.set_index(csv.columns[0])
    setting_val = csv.columns[1]
    return setting_key.at[key, setting_val]


##
# @brief \jp CSVから特定キーの値を取得する \en Get a specific key's value from a CSV
# @return \jp キーに対応する値 \en Value corresponding to the key
# @param csv \jp 読み込んだCSVデータ（DataFrame） \en Loaded CSV data (DataFrame)
# @param key \jp 取得したいキー \en Key to retrieve
##
def get_setting_type(csv: pd.DataFrame, key: str) -> str:
    setting_key = csv.set_index(csv.columns[0])
    setting_type = csv.columns[2]
    return setting_key.at[key, setting_type]


##
# @brief \jp CSVから特定キーの値を取得する \en Get a specific key's value from a CSV
# @return \jp キーに対応する値 \en Value corresponding to the key
# @param csv \jp 読み込んだCSVデータ（DataFrame） \en Loaded CSV data (DataFrame)
# @param key \jp 取得したいキー \en Key to retrieve
##
def get_setting_remark(csv: pd.DataFrame, key: str) -> str:
    setting_key = csv.set_index(csv.columns[0])
    setting_remark = csv.columns[3]
    return setting_key.at[key, setting_remark]


##
# @brief \jp CSVから特定キーの値を取得する \en Get a specific key's value from a CSV
# @return \jp キーに対応する値 \en Value corresponding to the key
# @param csv \jp 読み込んだCSVデータ（DataFrame） \en Loaded CSV data (DataFrame)
# @param key \jp 取得したいキー \en Key to retrieve
##
def get_setting_sql_table_item(
    csv: pd.DataFrame, groups: List[str]
) -> Dict[str, List[Tuple[str, str, str]]]:
    """
    ITM_*** 行を解析し、グループごとの列定義を返す。
    戻り値： { "RULES": [(col, type, remark), ...], "CAT_TYPE": [...], ... }
    """
    if pd is None:
        raise ImportError("pandas is required for get_setting_sql_table_item().")

    result: Dict[str, List[Tuple[str, str, str]]] = {g: [] for g in groups}

    for _, row in csv.iterrows():
        k = str(row.get("key", "")).strip()
        if not k.startswith("ITM_"):
            continue

        # ITM_RULES_... / ITM_CAT_TYPE_... をグループ化
        suffix = k[4:]  # remove "ITM_"
        parts = suffix.split("_")
        if len(parts) < 2:
            continue

        if parts[0] == "CAT":
            # CAT_TYPE / CAT_MAJOR / CAT_SUB / CAT_STATE ...
            group = f"CAT_{parts[1]}"
        else:
            # RULES ...
            group = parts[0]

        if group not in result:
            continue

        col_name = "" if pd.isna(row.get("value")) else str(row.get("value")).strip()
        type_str = "" if pd.isna(row.get("type")) else str(row.get("type")).strip()
        remark = "" if pd.isna(row.get("remark")) else str(row.get("remark")).strip()

        if not col_name:
            raise ValueError(f"Column name is empty for key={k!r}")

        # type が空のときの保険（key_ なら INTEGER、それ以外は TEXT）
        if not type_str:
            type_str = "INTEGER" if col_name.startswith("key_") else "TEXT"

        result[group].append((col_name, type_str, remark))

    for g, cols in result.items():
        if len(cols) == 0:
            raise ValueError(
                f"No column definitions found for group {g}. (Expected ITM_{g}_... rows)"
            )

    return result


##
# @if japanese
#   @brief setting.col_subv を DataFrame として読み込む。
#   @param filename  読み込むファイル名
#   @param data_dir  基準ディレクトリ（read_setting.py基準）
#   @param encoding  文字エンコーディング
#   @return DataFrame
# @endif
# @if english
# @brief Load setting.col_subv as a pandas DataFrame.
#   @param filename  LANG_EN File name
#   @param data_dir  Base directory (relative to read_setting.py)
#   @param encoding  Text encoding
#   @return DataFrame
# @endif
#
##
def load_setting_col_subv(
    *, filename: str = "setting.col_subv", data_dir: str = ".", encoding: str = "utf-8-sig"
):
    # 中身は CSV と同じ形式想定なので、既存の loader を流用する
    return load_setting_csv(filename=filename, data_dir=data_dir, encoding=encoding)
