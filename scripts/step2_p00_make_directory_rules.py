# -*- coding: utf-8 -*-
##
# @file scripts/step2_p00_make_directory_rules.py
# @brief Create rule folder hierarchy and manifest TSV from SQLite.
#
# @if japanese
# setting.csv とSQLite DBのカテゴリ・ルール情報を利用し、Type>Major>Sub>Rule(>Chapter)のフォルダ階層を作成します。
# 生成したディレクトリ構造をmanifest_rule_cap.tsvとして出力し、後続処理で参照できるようにします。
# DBとフォルダ構造のみを扱い、データ内容やロジックは変更しません。
# @endif
#
# @if english
# Uses setting.csv and SQLite category/rule data to build folder hierarchy Type>Major>Sub>Rule(>Chapter).
# Outputs the structure as manifest_rule_cap.tsv for downstream steps while creating directories on disk.
# Operates only on DB metadata and filesystem layout without altering business data.
# @endif
#

import re  # [JP] 標準: フォルダ名のサニタイズに使用 / [EN] Standard: sanitize folder names
import csv  # [JP] 標準: TSV出力 / [EN] Standard: TSV writing
import sqlite3  # [JP] 標準: SQLite接続 / [EN] Standard: SQLite connectivity
from pathlib import Path  # [JP] 標準: パス操作 / [EN] Standard: path utilities

import read_setting as rs  # [JP] 自作: 設定読込ユーティリティ / [EN] Local: load settings
import setting_key as sk  # [JP] 自作: 設定キー定数 / [EN] Local: setting key constants
import setting_helper as sh  # [JP] 自作: パス解決ヘルパ / [EN] Local: path helpers


##
# @brief Quote SQLite identifier / SQLite識別子をクオートする
#
# @if japanese
# テーブル名やカラム名をSQLite用にダブルクォートで括り、内部のダブルクォートはエスケープします。
# @endif
#
# @if english
# Wraps table/column names with double quotes for SQLite, escaping any embedded quotes.
# @endif
#
# @param name [in]  識別子文字列 / Identifier string
# @return str  クオート済み識別子 / Quoted identifier
def quote_ident(name: str) -> str:
    """
    SQLite identifier quote.
    """
    name = str(name).replace('"', '""')
    return f'"{name}"'


##
# @brief Sanitize folder segment / フォルダ名セグメントを安全化する
#
# @if japanese
# Noneや空文字、"nan"を"_"に置き換え、Windowsで禁止される文字や末尾のスペース・ドットを除去します。
# 最大80文字に切り詰め、安全なフォルダ名片を返します。
# @endif
#
# @if english
# Replace None/empty/"nan" with "_" and remove Windows-forbidden characters plus trailing dots/spaces.
# Truncates to 80 characters and returns a folder-safe segment.
# @endif
#
# @param s [in]  元の文字列 / Original string
# @return str  サニタイズ済みセグメント / Sanitized segment
def safe_segment(s: str) -> str:
    """
    Folder name safe segment (Windows-safe).
    """
    s = "" if s is None else str(s).strip()
    if s == "" or s.lower() == "nan":
        return "_"
    s = re.sub(r'[<>:"/\\|?*]', "_", s)
    s = s.rstrip(" .")  # Windows: 末尾のドット・スペースはNG
    return s[:80] if s else "_"


##
# @brief Pick first usable segment / 利用可能なセグメントを優先して選ぶ
#
# @if japanese
# 複数候補の中からsafe_segmentが"_"にならない最初の値を返します。全て"_"なら"_"を返します。
# @endif
#
# @if english
# Returns the first candidate that yields a non-"_" value via safe_segment; otherwise returns "_".
# @endif
#
# @param candidates [in]  候補文字列群 / Candidate values
# @return str  選択されたセグメント / Chosen segment
def pick_segment(*candidates) -> str:
    """
    candidates の中で最初に使えるものをsafe_segment にして返す
    """
    for c in candidates:
        seg = safe_segment(c)
        if seg != "_":
            return seg
    return "_"


##
# @brief Main entry: create rule directories and manifest / ルール用ディレクトリとマニフェストを生成する
#
# @if japanese
# setting.csv を読み込みDBパスと各テーブル/カラム名を取得し、カテゴリ階層とルール情報をSQLで取得します。
# Type>Major>Sub>Rule(>Chapter)のフォルダを作成し、生成結果をmanifest_rule_cap.tsvに書き出します。
# DB未存在時は処理を中止し、出力パス情報と作成数を標準出力に表示します。
# @endif
#
# @if english
# Loads setting.csv to resolve DB/table/column names, fetches category and rule hierarchy via SQL,
# creates directories for Type>Major>Sub>Rule(>Chapter), and writes manifest_rule_cap.tsv.
# Stops early when the DB is missing and prints output paths plus created directory counts.
# @endif
#
# @details
# @if japanese
# - DBパスを解決し、存在チェックを行う。
# - 出力ルートとマニフェストパスを準備しディレクトリを作成する。
# - テーブル・カラム名を設定から取得し、階層用のSQLを組み立てる。
# - SQL結果を走査してフォルダを作成し、TSVに書き出す。
# - 最終的な出力パスと作成数をログ表示する。
# @endif
# @if english
# - Resolve DB path and verify existence.
# - Prepare output root and manifest path, ensuring directories exist.
# - Obtain table/column names from settings and build the hierarchy SQL.
# - Iterate query results to create folders and write the TSV manifest.
# - Log output paths and directory creation counts.
# @endif
#
def main():
    setting_csv = rs.load_setting_csv()
    print(setting_csv)

    # [JP] DBパスを解決し存在を確認 / [EN] Resolve DB path and check existence
    db_name = rs.get_setting_value(setting_csv, sk.KEY_DB_NAME)
    DB_PATH = Path(sh.rules_file_fullpath(setting_csv, db_name))  # 作成されるSQLite ファイル
    if not DB_PATH.exists():
        print("DB not found:", DB_PATH)
        return

    # [JP] 出力ルートとマニフェストパスを準備 / [EN] Prepare output root and manifest path
    out_root = Path(sh.rules_file_dir_path(setting_csv))
    print(out_root)
    manifest_path = Path(out_root._str + "/manifest_rule_cap.tsv")
    out_root.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    # [JP] テーブル名を設定から取得 / [EN] Fetch table names from settings
    tbl_cat_type = rs.get_setting_value(setting_csv, sk.KEY_TBL_CAT_TYPE)
    tbl_cat_major = rs.get_setting_value(setting_csv, sk.KEY_TBL_CAT_MAJOR)
    tbl_cat_sub = rs.get_setting_value(setting_csv, sk.KEY_TBL_CAT_SUB)
    tbl_rules = rs.get_setting_value(setting_csv, sk.KEY_TBL_RULES)
    tbl_request = rs.get_setting_value(setting_csv, sk.KEY_TBL_REQUEST)

    # [JP] カラム名を設定から取得 / [EN] Fetch column names from settings
    ct_pkey = rs.get_setting_value(setting_csv, sk.KEY_ITM_CAT_TYPE_PKEY)
    ct_title = rs.get_setting_value(setting_csv, sk.KEY_ITM_CAT_TYPE_TITLE_EN)  # フォールバック用
    ct_path = rs.get_setting_value(setting_csv, sk.KEY_ITM_CAT_TYPE_PATH)

    cm_pkey = rs.get_setting_value(setting_csv, sk.KEY_ITM_CAT_MAJOR_PKEY)
    cm_title = rs.get_setting_value(setting_csv, sk.KEY_ITM_CAT_MAJOR_TITLE_EN)
    cm_fkey = rs.get_setting_value(setting_csv, sk.KEY_ITM_CAT_MAJOR_FKEY_CAT_TYPE)
    cm_path = rs.get_setting_value(setting_csv, sk.KEY_ITM_CAT_MAJOR_PATH)

    cs_pkey = rs.get_setting_value(setting_csv, sk.KEY_ITM_CAT_SUB_PKEY)
    cs_title = rs.get_setting_value(setting_csv, sk.KEY_ITM_CAT_SUB_TITLE_EN)
    cs_fkey = rs.get_setting_value(setting_csv, sk.KEY_ITM_CAT_SUB_FKEY_CAT_MAJOR)
    cs_path = rs.get_setting_value(setting_csv, sk.KEY_ITM_CAT_SUB_PATH)

    r_pkey = rs.get_setting_value(setting_csv, sk.KEY_ITM_RULES_PKEY)
    r_id_rule = rs.get_setting_value(setting_csv, sk.KEY_ITM_RULES_ID_RULE)
    r_fkey_cs = rs.get_setting_value(setting_csv, sk.KEY_ITM_RULES_FKEY_CAT_SUB)

    req_key_rule = rs.get_setting_value(setting_csv, sk.KEY_ITM_REQUEST_KEY_RULE)
    req_id_cap = rs.get_setting_value(setting_csv, sk.KEY_ITM_REQUEST_ID_CAP)

    # [JP] SQL組み立て（Type > Major > Sub > Rule > Chapter） / [EN] Build SQL for hierarchy
    sql = f"""
    WITH caps AS (
        SELECT DISTINCT
            CAST(req.{quote_ident(req_key_rule)} AS INTEGER) AS key_rule_int,
            req.{quote_ident(req_id_cap)} AS id_cap
        FROM {quote_ident(tbl_request)} AS req
        WHERE req.{quote_ident(req_id_cap)} IS NOT NULL
          AND TRIM(req.{quote_ident(req_id_cap)}) <> ''
    )
    SELECT
        ct.{quote_ident(ct_path)}  AS type_path,
        ct.{quote_ident(ct_title)} AS type_title_en,
        ct.{quote_ident(ct_pkey)}  AS key_cat_type,

        cm.{quote_ident(cm_path)}  AS major_path,
        cm.{quote_ident(cm_title)} AS major_title_en,
        cm.{quote_ident(cm_pkey)}  AS key_cat_major,

        cs.{quote_ident(cs_path)}  AS sub_path,
        cs.{quote_ident(cs_title)} AS sub_title_en,
        cs.{quote_ident(cs_pkey)}  AS key_cat_sub,

        r.{quote_ident(r_pkey)}    AS key_rule,
        r.{quote_ident(r_id_rule)} AS id_rule,

        caps.id_cap                AS id_cap
    FROM {quote_ident(tbl_rules)} AS r
    JOIN {quote_ident(tbl_cat_sub)} AS cs
      ON cs.{quote_ident(cs_pkey)} = r.{quote_ident(r_fkey_cs)}
    JOIN {quote_ident(tbl_cat_major)} AS cm
      ON cm.{quote_ident(cm_pkey)} = cs.{quote_ident(cs_fkey)}
    JOIN {quote_ident(tbl_cat_type)} AS ct
      ON ct.{quote_ident(ct_pkey)} = cm.{quote_ident(cm_fkey)}
    LEFT JOIN caps
      ON caps.key_rule_int = r.{quote_ident(r_pkey)}
    ORDER BY
        ct.{quote_ident(ct_pkey)},
        cm.{quote_ident(cm_pkey)},
        cs.{quote_ident(cs_pkey)},
        r.{quote_ident(r_id_rule)},
        caps.id_cap
    ;
    """

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # [JP] SQL実行と結果取得 / [EN] Execute SQL and fetch rows
    rows = cur.execute(sql).fetchall()
    print("rows:", len(rows))

    made_dirs = 0

    # [JP] マニフェストTSVへ書き出し / [EN] Write results to manifest TSV
    with manifest_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(
            ["type_path", "major_path", "sub_path", "id_rule", "key_rule", "id_cap", "out_dir"]
        )

        for r in rows:
            type_seg = pick_segment(r["type_path"], r["type_title_en"], r["key_cat_type"])
            major_seg = pick_segment(r["major_path"], r["major_title_en"], r["key_cat_major"])
            sub_seg = pick_segment(r["sub_path"], r["sub_title_en"], r["key_cat_sub"])

            id_rule_seg = safe_segment(r["id_rule"])
            base_dir = out_root / type_seg / major_seg / sub_seg / id_rule_seg

            id_cap = r["id_cap"]
            if id_cap is None or str(id_cap).strip() == "":
                out_dir = base_dir
            else:
                out_dir = base_dir / safe_segment(id_cap)

            if not out_dir.exists():
                out_dir.mkdir(parents=True, exist_ok=True)
                made_dirs += 1
            else:
                out_dir.mkdir(parents=True, exist_ok=True)

            w.writerow(
                [
                    type_seg,
                    major_seg,
                    sub_seg,
                    r["id_rule"],
                    r["key_rule"],
                    id_cap or "",
                    str(out_dir),
                ]
            )

    conn.close()

    # [JP] 出力情報を表示 / [EN] Print output summary
    print("OUT_ROOT      :", out_root)
    print("MANIFEST_PATH :", manifest_path)
    print("mkdir created :", made_dirs)
    print("done")


if __name__ == "__main__":
    main()
