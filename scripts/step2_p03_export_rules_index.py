# -*- coding: utf-8 -*-
##
# @file scripts/step2_p03_export_rules_index.py
# @brief Generate rules_index.json/csv for list views.
#
# @if japanese
# manifest_rule_cap.tsv と SQLite のルール・カテゴリ情報を組み合わせ、一覧表示用JSON/CSVを生成します。
# setting.csv のキーが存在しない場合でもフォールバック値で動作し、MDファイルへのパスも計算して含めます。
# 出力先は設定から解決し、処理状況を標準出力へ表示します。
# @endif
#
# @if english
# Combines manifest_rule_cap.tsv with SQLite rule and category data to produce list-view JSON/CSV artifacts.
# Works with fallback values when some setting keys are absent and computes MD file paths for each rule.
# Resolves output location from settings and logs progress to stdout.
# @endif
#
"""
@file step2_p03_export_rules_index.py
@brief Step2-4: 一覧表示や表パーツ用データ(rules_index.json/csv)を生成する。
"""

from __future__ import annotations

import argparse  # [JP] 標準: CLI引数処理 / [EN] Standard: CLI argument parsing
import csv  # [JP] 標準: TSV/CSV処理 / [EN] Standard: TSV/CSV handling
import json  # [JP] 標準: JSON出力 / [EN] Standard: JSON output
import sqlite3  # [JP] 標準: SQLite接続 / [EN] Standard: SQLite connectivity
from dataclasses import dataclass  # [JP] 標準: dataclass定義 / [EN] Standard: dataclass
from pathlib import Path  # [JP] 標準: パス操作 / [EN] Standard: path handling
from typing import Any, Dict, List, Optional  # [JP] 標準: 型ヒント / [EN] Standard: type hints
import csv  # [JP] 標準: 重複インポート（元コード踏襲） / [EN] Standard: duplicate import kept
import sqlite3  # [JP] 標準: 重複インポート（元コード踏襲） / [EN] Standard: duplicate import kept

try:
    import pandas as pd  # [JP] 外部: DataFrame処理（任意依存） / [EN] External: DataFrame support (optional)
except ImportError:
    pd = None  # type: ignore


# ---- project modules ----
import setting_key as sk  # [JP] 自作: 設定キー定数 / [EN] Local: setting keys
import read_setting as rs  # [JP] 自作: 設定読込 / [EN] Local: settings loader
import setting_helper as sh  # [JP] 自作: パス解決ヘルパ / [EN] Local: path helpers


# ---- defaults (setting.csv / setting_key.py に無くても動くためのフォールバック) ----
DEFAULT_MANIFEST_TSV_NAME: str = "manifest_rule_cap.tsv"
DEFAULT_RULES_INDEX_JSON_NAME: str = "rules_index.json"
DEFAULT_RULES_INDEX_CSV_NAME: str = "rules_index.csv"
DEFAULT_RULE_MD_FILENAME: str = "rule.md"


# ---- optional new keys (あれば使う) ----
KEY_TSV_MANIFEST_RULE_CAP: str = "TSV_MANIFEST_RULE_CAP"
KEY_JSON_RULES_INDEX: str = "JSON_RULES_INDEX"
KEY_MD_RULE_FILENAME: str = "MD_RULE_FILENAME"


@dataclass(frozen=True)
class ManifestRuleInfo:
    """Manifest information per rule."""

    type_path: str
    major_path: str
    sub_path: str
    id_rule: str
    key_rule: str
    rule_dir: Path
    cap_count: int


##
# @brief Get setting value with fallback / 設定値をフォールバック付きで取得する
#
# @if japanese
# setting_key.py に定数が無い場合でも setting.csv を直接参照し、存在しなければデフォルト値を返します。
# @endif
#
# @if english
# Reads a value from setting.csv directly, returning a default when the key is missing or lookup fails.
# @endif
#
# @param setting_csv [in]  設定DataFrame / Settings DataFrame
# @param key_name [in]  キー名 / Key name
# @param default_value [in]  フォールバック値 / Fallback value
# @return str  取得した値またはデフォルト / Retrieved value or default
def _get_setting_or_default(setting_csv: Path, key_name: str, default_value: str) -> str:
    """
    setting_key.py に定数が無くても、setting.csv を直接参照して値を取りたい。
    ただしread_setting.get_setting_value は key 名で引けるので、存在しなければ default。
    """
    try:
        return rs.get_setting_value(setting_csv, key_name)
    except Exception:
        return default_value


##
# @brief Load manifest_rule_cap.tsv and index by id_rule / manifest_rule_cap.tsv を読み込みid_ruleで引ける辞書を作る
#
# @if japanese
# Step2-1で生成されたmanifest_rule_cap.tsvを読み込み、id_ruleをキーとしたManifestRuleInfo辞書を返します。
# TSVの必須ヘッダを検証し、id_capの有無でrule_dirとcap_countを適切に設定します。
# @endif
#
# @if english
# Reads manifest_rule_cap.tsv created in Step2-1 and returns a dictionary keyed by id_rule with ManifestRuleInfo values.
# Validates required headers and normalizes rule_dir/cap_count depending on presence of id_cap.
# @endif
#
# @param setting_csv [in]  設定DataFrame / Settings DataFrame
# @return Dict[str, ManifestRuleInfo]  id_rule -> ManifestRuleInfo の辞書 / Mapping from id_rule to ManifestRuleInfo
def _load_manifest_rule_dirs(setting_csv: Path) -> Dict[str, ManifestRuleInfo]:
    """
    Step2-1 が出力したmanifest_rule_cap.tsv を読み込み、
    id_rule -> ルールディレクトリ を復元する。
    manifest の列 type_path, major_path, sub_path, id_rule, key_rule, id_cap, out_dir:contentReference[oaicite:2]{index=2}
    """
    out_root = Path(sh.rules_file_dir_path(setting_csv))  # build/.../rules/<RULES_FILE_DIR> の想定
    manifest_name = _get_setting_or_default(
        setting_csv, KEY_TSV_MANIFEST_RULE_CAP, DEFAULT_MANIFEST_TSV_NAME
    )
    manifest_path = out_root / manifest_name

    if not manifest_path.exists():
        raise FileNotFoundError(f"manifest not found: {manifest_path}")

    by_rule: Dict[str, ManifestRuleInfo] = {}

    # [JP] TSVを読み込み必須列を確認 / [EN] Read TSV and validate required headers
    with manifest_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        required = {
            "type_path",
            "major_path",
            "sub_path",
            "id_rule",
            "key_rule",
            "id_cap",
            "out_dir",
        }
        if reader.fieldnames is None or not required.issubset(set(reader.fieldnames)):
            raise ValueError(
                f"manifest header mismatch. required={sorted(required)} got={reader.fieldnames}"
            )

        # [JP] 各行を走査してrule_dirとcap_countを計算 / [EN] Iterate rows to compute rule_dir and cap_count
        for row in reader:
            id_rule = (row.get("id_rule") or "").strip()
            if not id_rule:
                continue

            id_cap = (row.get("id_cap") or "").strip()
            out_dir = Path((row.get("out_dir") or "").strip())
            if not out_dir:
                continue

            # [JP] id_capの有無でrule_dirを正規化 / [EN] Normalize rule_dir depending on id_cap presence
            rule_dir = out_dir if id_cap == "" else out_dir.parent

            info = by_rule.get(id_rule)
            if info is None:
                by_rule[id_rule] = ManifestRuleInfo(
                    type_path=(row.get("type_path") or "").strip(),
                    major_path=(row.get("major_path") or "").strip(),
                    sub_path=(row.get("sub_path") or "").strip(),
                    id_rule=id_rule,
                    key_rule=(row.get("key_rule") or "").strip(),
                    rule_dir=rule_dir,
                    cap_count=1 if id_cap else 0,
                )
            else:
                cap_count = info.cap_count + (1 if id_cap else 0)
                # 同一id_ruleで rule_dir がブレるのはおかしいが、あっても最初を優先して継続
                by_rule[id_rule] = ManifestRuleInfo(
                    type_path=info.type_path,
                    major_path=info.major_path,
                    sub_path=info.sub_path,
                    id_rule=info.id_rule,
                    key_rule=info.key_rule,
                    rule_dir=info.rule_dir,
                    cap_count=cap_count,
                )

    return by_rule


##
# @brief Fetch flat rule list from DB / DBから一覧用フラットデータを取得する
#
# @if japanese
# setting.csv からテーブル・カラム名を取得し、ルール基本情報とカテゴリ・状態の関連情報をJOINでまとめて返します。
# SQLを標準出力へ出力し、結果を辞書のリストとして返します。
# @endif
#
# @if english
# Reads table/column names from settings, queries rule basics plus category/state joins, and returns a list of dictionaries.
# Prints the generated SQL to stdout for visibility.
# @endif
#
# @param setting_csv [in]  設定DataFrame / Settings DataFrame
# @return List[Dict[str, Any]]  取得結果リスト / List of result dictionaries
def _fetch_rules_flat(setting_csv: Path) -> List[Dict[str, Any]]:
    """
    DBから一覧用のフラット行を取得（カテゴリ + 状態 + ルール基本行）。
    列名・テーブル名は setting.csv から取得する。
    """
    db_name = rs.get_setting_value(setting_csv, sk.KEY_DB_NAME)
    db_path = Path(sh.rules_file_fullpath(setting_csv, db_name))

    # [JP] テーブル名 / [EN] Table names
    tbl_rules = rs.get_setting_value(setting_csv, sk.KEY_TBL_RULES)
    tbl_cat_type = rs.get_setting_value(setting_csv, sk.KEY_TBL_CAT_TYPE)
    tbl_cat_major = rs.get_setting_value(setting_csv, sk.KEY_TBL_CAT_MAJOR)
    tbl_cat_sub = rs.get_setting_value(setting_csv, sk.KEY_TBL_CAT_SUB)
    tbl_cat_state = rs.get_setting_value(setting_csv, sk.KEY_TBL_CAT_STATE)

    # [JP] カラム名（ルール） / [EN] Column names (rules)
    c_rules_pkey = rs.get_setting_value(setting_csv, sk.KEY_ITM_RULES_PKEY)
    c_rules_id = rs.get_setting_value(setting_csv, sk.KEY_ITM_RULES_ID_RULE)
    c_rules_name = rs.get_setting_value(setting_csv, sk.KEY_ITM_RULES_NAME_RULE)
    c_rules_fkey_sub = rs.get_setting_value(setting_csv, sk.KEY_ITM_RULES_FKEY_CAT_SUB)
    c_rules_link = rs.get_setting_value(setting_csv, sk.KEY_ITM_RULES_LINK)
    c_rules_fkey_state = rs.get_setting_value(setting_csv, sk.KEY_ITM_RULES_FKEY_CAT_STATE)
    c_rules_created = rs.get_setting_value(setting_csv, sk.KEY_ITM_RULES_CREATED_DATE)
    c_rules_update = rs.get_setting_value(setting_csv, sk.KEY_ITM_RULES_UPDATE_DATE)

    # [JP] カラム名（Type/Major/Sub/State） / [EN] Column names (Type/Major/Sub/State)
    c_type_pkey = rs.get_setting_value(setting_csv, sk.KEY_ITM_CAT_TYPE_PKEY)
    c_type_tjp = rs.get_setting_value(setting_csv, sk.KEY_ITM_CAT_TYPE_TITLE_JP)
    c_type_ten = rs.get_setting_value(setting_csv, sk.KEY_ITM_CAT_TYPE_TITLE_EN)
    c_type_path = rs.get_setting_value(setting_csv, sk.KEY_ITM_CAT_TYPE_PATH)

    c_major_pkey = rs.get_setting_value(setting_csv, sk.KEY_ITM_CAT_MAJOR_PKEY)
    c_major_tjp = rs.get_setting_value(setting_csv, sk.KEY_ITM_CAT_MAJOR_TITLE_JP)
    c_major_ten = rs.get_setting_value(setting_csv, sk.KEY_ITM_CAT_MAJOR_TITLE_EN)
    c_major_fkey_type = rs.get_setting_value(setting_csv, sk.KEY_ITM_CAT_MAJOR_FKEY_CAT_TYPE)
    c_major_path = rs.get_setting_value(setting_csv, sk.KEY_ITM_CAT_MAJOR_PATH)

    c_sub_pkey = rs.get_setting_value(setting_csv, sk.KEY_ITM_CAT_SUB_PKEY)
    c_sub_tjp = rs.get_setting_value(setting_csv, sk.KEY_ITM_CAT_SUB_TITLE_JP)
    c_sub_ten = rs.get_setting_value(setting_csv, sk.KEY_ITM_CAT_SUB_TITLE_EN)
    c_sub_fkey_major = rs.get_setting_value(setting_csv, sk.KEY_ITM_CAT_SUB_FKEY_CAT_MAJOR)
    c_sub_path = rs.get_setting_value(setting_csv, sk.KEY_ITM_CAT_SUB_PATH)

    c_state_pkey = rs.get_setting_value(setting_csv, sk.KEY_ITM_CAT_STATE_PKEY)
    c_state_tjp = rs.get_setting_value(setting_csv, sk.KEY_ITM_CAT_STATE_TITLE_JP)
    c_state_ten = rs.get_setting_value(setting_csv, sk.KEY_ITM_CAT_STATE_TITLE_EN)

    sql = f"""
SELECT
  r.{c_rules_pkey}       AS pkey_rule,
  r.{c_rules_id}         AS id_rule,
  r.{c_rules_name}       AS title_rule,
  r.{c_rules_link}       AS link_db,
  r.{c_rules_created}    AS created_date,
  r.{c_rules_update}     AS update_date,

  st.{c_state_pkey}      AS key_state,
  st.{c_state_tjp}       AS state_jp,
  st.{c_state_ten}       AS state_en,

  ty.{c_type_pkey}       AS key_type,
  ty.{c_type_tjp}        AS type_jp,
  ty.{c_type_ten}        AS type_en,
  ty.{c_type_path}       AS type_path,

  mj.{c_major_pkey}      AS key_major,
  mj.{c_major_tjp}       AS major_jp,
  mj.{c_major_ten}       AS major_en,
  mj.{c_major_path}      AS major_path,

  sb.{c_sub_pkey}        AS key_sub,
  sb.{c_sub_tjp}         AS sub_jp,
  sb.{c_sub_ten}         AS sub_en,
  sb.{c_sub_path}        AS sub_path

FROM {tbl_rules} r
LEFT JOIN {tbl_cat_sub} sb
  ON r.{c_rules_fkey_sub} = sb.{c_sub_pkey}
LEFT JOIN {tbl_cat_major} mj
  ON sb.{c_sub_fkey_major} = mj.{c_major_pkey}
LEFT JOIN {tbl_cat_type} ty
  ON mj.{c_major_fkey_type} = ty.{c_type_pkey}
LEFT JOIN {tbl_cat_state} st
  ON r.{c_rules_fkey_state} = st.{c_state_pkey}
ORDER BY
  ty.{c_type_pkey}, mj.{c_major_pkey}, sb.{c_sub_pkey}, r.{c_rules_id}
""".strip()

    print(f"SQL:\n {sql}")

    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    try:
        cur = con.execute(sql)
        return [dict(r) for r in cur.fetchall()]
    finally:
        con.close()


##
# @brief Build and export rules index JSON / ルール一覧JSONを生成して出力する
#
# @if japanese
# manifest_rule_cap.tsvからフォルダ情報を取得し、DBのルール一覧と結合してJSONを生成します。
# MDファイルの相対パスとリンク、章数、作成・更新日や状態ラベルを含め、指定パスへ書き出します。
# @endif
#
# @if english
# Loads folder info from manifest_rule_cap.tsv, combines it with DB rule listings, and writes the resulting JSON.
# Includes relative MD paths, links, chapter counts, created/updated dates, and state labels before saving to the target path.
# @endif
#
# @param setting_csv [in]  設定DataFrame / Settings DataFrame
# @param out_path [in]  出力先パス / Output path
# @details
# @if japanese
# - manifestを読み込みid_rule -> rule_dir辞書を作る。
# - DBからルール一覧を取得する。
# - rules_dir/rules_file_dirを組み合わせてMDパスを計算する。
# - 日本語優先のラベルを選び、章数などの付加情報をまとめる。
# - JSONとしてファイル出力し、件数をログ表示する。
# @endif
# @if english
# - Load manifest to map id_rule to rule_dir.
# - Fetch flat rule list from the DB.
# - Compute MD paths using rules_dir and rules_file_dir.
# - Select labels (preferring Japanese), aggregate chapter counts, and other metadata.
# - Write the JSON file and log the number of items.
# @endif
#
def export_rules_index(setting_csv: Path, out_path: Path) -> None:
    manifest_by_id: Dict[str, ManifestRuleInfo] = _load_manifest_rule_dirs(setting_csv)
    rows = _fetch_rules_flat(setting_csv)

    # [JP] パス構築用の設定を取得 / [EN] Retrieve settings for path construction
    rules_dir = rs.get_setting_value(setting_csv, sk.KEY_RULES_DIR)
    rules_file_dir = rs.get_setting_value(setting_csv, sk.KEY_RULES_FILE_DIR)
    md_filename = _get_setting_or_default(
        setting_csv, KEY_MD_RULE_FILENAME, DEFAULT_RULE_MD_FILENAME
    )

    # [JP] rules_file_dir が空/ドットなら省略して接頭辞に / [EN] Omit rules_file_dir when empty/dot
    def _prefix() -> str:
        rf = (rules_file_dir or "").strip()
        if rf in ("", "."):
            return f"{rules_dir}"
        return f"{rules_dir}/{rf}"

    prefix = _prefix()

    items: List[Dict[str, Any]] = []
    for r in rows:
        id_rule = str(r.get("id_rule") or "")
        info = manifest_by_id.get(id_rule)

        # [JP] ラベルは日本語優先 / [EN] Prefer Japanese labels
        def _lab(jp: Any, en: Any, key: Any) -> str:
            v = jp if jp not in (None, "") else en if en not in (None, "") else key
            return "" if v is None else str(v)

        state = _lab(r.get("state_jp"), r.get("state_en"), r.get("key_state"))
        type_label = _lab(r.get("type_jp"), r.get("type_en"), r.get("key_type"))
        major_label = _lab(r.get("major_jp"), r.get("major_en"), r.get("key_major"))
        sub_label = _lab(r.get("sub_jp"), r.get("sub_en"), r.get("key_sub"))

        # [JP] md_path / link はmanifest優先、無ければDBのpath列から復元 / [EN] Prefer manifest paths, fall back to DB path columns
        if info is not None:
            rel_dir = f"{info.type_path}/{info.major_path}/{info.sub_path}/{info.id_rule}"
        else:
            rel_dir = f"{r.get('type_path')}/{r.get('major_path')}/{r.get('sub_path')}/{id_rule}"

        rel_dir = rel_dir.replace("\\", "/").strip("/")

        md_path = f"{prefix}/{rel_dir}/{md_filename}".replace("\\", "/")
        link = md_path  # HTML側はこのpathでfetchする想定
        items.append(
            {
                "id_rule": id_rule,
                "key_rule": str(r.get("pkey_rule") or (info.key_rule if info else "")),
                "title_rule": str(r.get("title_rule") or ""),
                "state": state,
                "key_type": str(r.get("key_type") or ""),
                "type": type_label,
                "key_major": str(r.get("key_major") or ""),
                "major": major_label,
                "key_sub": str(r.get("key_sub") or ""),
                "sub": sub_label,
                "md_path": md_path,
                "link": link,
                "cap_count": int(info.cap_count) if info else 0,
                "created_date": r.get("created_date"),
                "update_date": r.get("update_date"),
                "link_db": r.get("link_db"),
            }
        )

    print(out_path)
    print(items)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[OK] exported: {out_path} ({len(items)} rows)")


##
# @brief CLI entry point / CLIエントリーポイント
#
# @if japanese
# setting.csv を読み込み、出力先パスを解決してexport_rules_indexを実行します。
# @endif
#
# @if english
# Loads settings, resolves the output path, and runs export_rules_index.
# @endif
#
# @return int  終了コード / Exit code
def main() -> int:
    setting_csv = rs.load_setting_csv()
    print(setting_csv)

    out_path = Path(
        sh.json_file_fullpath(
            setting_csv, rs.get_setting_value(setting_csv, sk.KEY_JSON_MAIN_INDEX)
        )
    )
    print(f"Out path: {out_path}")

    export_rules_index(setting_csv, out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
