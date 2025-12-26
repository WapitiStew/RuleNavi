# -*- coding: utf-8 -*-
"""
@file step2_p03_export_rules_index.py
@brief Step2-4: 一覧表示（表パーツ）用データ(rules_index.json/csv)を生成する。
"""

from __future__ import annotations

import argparse
import csv
import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional
import csv
import sqlite3

try:
    import pandas as pd
except ImportError:
    pd = None


# ---- project modules ----
import setting_key as sk
import read_setting as rs
import setting_helper as sh


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
    type_path: str
    major_path: str
    sub_path: str
    id_rule: str
    key_rule: str
    rule_dir: Path
    cap_count: int


def _get_setting_or_default(setting_csv: Path, key_name: str, default_value: str) -> str:
    """
    setting_key.py に定数が無いキーでも、setting.csv を直接参照して値を取りたい。
    ただし read_setting.get_setting_value は key 名で引けるので、存在しなければ default。
    """
    try:
        return rs.get_setting_value(setting_csv, key_name)
    except Exception:
        return default_value


def _load_manifest_rule_dirs(setting_csv: Path) -> Dict[str, ManifestRuleInfo]:
    """
    Step2-1 が出力した manifest_rule_cap.tsv を読み込み、
    id_rule -> ルールディレクトリ を復元する。

    manifest の列: type_path, major_path, sub_path, id_rule, key_rule, id_cap, out_dir:contentReference[oaicite:2]{index=2}
    """
    out_root = Path(sh.rules_file_dir_path(setting_csv))  # build/.../rules/<RULES_FILE_DIR> の想定
    manifest_name = _get_setting_or_default(setting_csv, KEY_TSV_MANIFEST_RULE_CAP, DEFAULT_MANIFEST_TSV_NAME)
    manifest_path = out_root / manifest_name

    if not manifest_path.exists():
        raise FileNotFoundError(f"manifest not found: {manifest_path}")

    by_rule: Dict[str, ManifestRuleInfo] = {}

    with manifest_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        required = {"type_path", "major_path", "sub_path", "id_rule", "key_rule", "id_cap", "out_dir"}
        if reader.fieldnames is None or not required.issubset(set(reader.fieldnames)):
            raise ValueError(f"manifest header mismatch. required={sorted(required)} got={reader.fieldnames}")

        for row in reader:
            id_rule = (row.get("id_rule") or "").strip()
            if not id_rule:
                continue

            id_cap = (row.get("id_cap") or "").strip()
            out_dir = Path((row.get("out_dir") or "").strip())
            if not out_dir:
                continue

            # out_dir は「id_cap が空なら rule dir」「id_cap があるなら cap dir」なので rule dir に正規化
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


def _fetch_rules_flat(setting_csv: Path) -> List[Dict[str, Any]]:
    """
    DBから一覧用のフラット情報を取得（分類 + 状態 + ルール基本情報）。
    列名・テーブル名は setting.csv から取得する。
    """
    db_name = rs.get_setting_value(setting_csv, sk.KEY_DB_NAME)
    db_path = Path(sh.rules_file_fullpath(setting_csv, db_name))

    tbl_rules = rs.get_setting_value(setting_csv, sk.KEY_TBL_RULES)
    tbl_cat_type = rs.get_setting_value(setting_csv, sk.KEY_TBL_CAT_TYPE)
    tbl_cat_major = rs.get_setting_value(setting_csv, sk.KEY_TBL_CAT_MAJOR)
    tbl_cat_sub = rs.get_setting_value(setting_csv, sk.KEY_TBL_CAT_SUB)
    tbl_cat_state = rs.get_setting_value(setting_csv, sk.KEY_TBL_CAT_STATE)

    c_rules_pkey = rs.get_setting_value(setting_csv, sk.KEY_ITM_RULES_PKEY)
    c_rules_id = rs.get_setting_value(setting_csv, sk.KEY_ITM_RULES_ID_RULE)
    c_rules_name = rs.get_setting_value(setting_csv, sk.KEY_ITM_RULES_NAME_RULE)
    c_rules_fkey_sub = rs.get_setting_value(setting_csv, sk.KEY_ITM_RULES_FKEY_CAT_SUB)
    c_rules_link = rs.get_setting_value(setting_csv, sk.KEY_ITM_RULES_LINK)
    c_rules_fkey_state = rs.get_setting_value(setting_csv, sk.KEY_ITM_RULES_FKEY_CAT_STATE)
    c_rules_created = rs.get_setting_value(setting_csv, sk.KEY_ITM_RULES_CREATED_DATE)
    c_rules_update = rs.get_setting_value(setting_csv, sk.KEY_ITM_RULES_UPDATE_DATE)

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


def export_rules_index(setting_csv: Path, out_path: Path ) -> None:
    manifest_by_id: Dict[str, ManifestRuleInfo] = _load_manifest_rule_dirs(setting_csv)
    rows = _fetch_rules_flat(setting_csv)

    # パス組み立て
    rules_dir = rs.get_setting_value(setting_csv, sk.KEY_RULES_DIR)
    rules_file_dir = rs.get_setting_value(setting_csv, sk.KEY_RULES_FILE_DIR)
    md_filename = _get_setting_or_default(setting_csv, KEY_MD_RULE_FILENAME, DEFAULT_RULE_MD_FILENAME)

    # rules_file_dir が空/ドットなら省略して整える
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

        # ラベルは日本語優先、無ければ英語、無ければキー
        def _lab(jp: Any, en: Any, key: Any) -> str:
            v = jp if jp not in (None, "") else en if en not in (None, "") else key
            return "" if v is None else str(v)

        state = _lab(r.get("state_jp"), r.get("state_en"), r.get("key_state"))
        type_label = _lab(r.get("type_jp"), r.get("type_en"), r.get("key_type"))
        major_label = _lab(r.get("major_jp"), r.get("major_en"), r.get("key_major"))
        sub_label = _lab(r.get("sub_jp"), r.get("sub_en"), r.get("key_sub"))

        # md_path / link（基本は manifest 優先。無ければ DB の path 列で復元）
        if info is not None:
            # manifest の type/major/sub は既にフォルダ用（サニタイズ済み）を想定
            rel_dir = f"{info.type_path}/{info.major_path}/{info.sub_path}/{info.id_rule}"
        else:
            rel_dir = f"{r.get('type_path')}/{r.get('major_path')}/{r.get('sub_path')}/{id_rule}"

        rel_dir = rel_dir.replace("\\", "/").strip("/")

        md_path = f"{prefix}/{rel_dir}/{md_filename}".replace("\\", "/")
        link = md_path  # HTML側はこの path を fetch して表示する想定

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


def main() -> int:

    setting_csv = rs.load_setting_csv()
    print( setting_csv )

    out_path = Path( sh.json_file_fullpath( setting_csv, rs.get_setting_value( setting_csv, sk.KEY_JSON_MAIN_INDEX ) ) )
    print( f"Out path: {out_path}" )

    export_rules_index(setting_csv, out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
