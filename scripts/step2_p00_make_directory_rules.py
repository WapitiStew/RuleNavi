import re
import csv
import sqlite3
from pathlib import Path

import read_setting as rs
import setting_key as sk
import setting_helper as sh


def quote_ident(name: str) -> str:
    """
    SQLite identifier quote.
    """
    name = str(name).replace('"', '""')
    return f'"{name}"'


def safe_segment(s: str) -> str:
    """
    Folder name safe segment (Windows-safe).
    """
    s = "" if s is None else str(s).strip()
    if s == "" or s.lower() == "nan":
        return "_"
    s = re.sub(r'[<>:"/\\|?*]', "_", s)
    s = s.rstrip(" .")  # Windows: 末尾のドット/スペースはNG
    return s[:80] if s else "_"


def pick_segment(*candidates) -> str:
    """
    candidates のうち最初に使えるものを safe_segment にして返す
    """
    for c in candidates:
        seg = safe_segment(c)
        if seg != "_":
            return seg
    return "_"


def main():
    setting_csv = rs.load_setting_csv()
    print(setting_csv)

    # DBパス
    db_name = rs.get_setting_value(setting_csv, sk.KEY_DB_NAME)
    DB_PATH = Path(sh.rules_file_fullpath(setting_csv, db_name))  # 作成される SQLite ファイル
    if not DB_PATH.exists():
        print("DB not found:", DB_PATH)
        return

    # ---- 出力先（まずは固定でOK。必要なら後で setting.csv に移す）----
    out_root = Path(sh.rules_file_dir_path(setting_csv))
    print(out_root)
    manifest_path = Path(out_root._str + "/manifest_rule_cap.tsv")
    out_root.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    # ---- テーブル名 ----
    tbl_cat_type = rs.get_setting_value(setting_csv, sk.KEY_TBL_CAT_TYPE)
    tbl_cat_major = rs.get_setting_value(setting_csv, sk.KEY_TBL_CAT_MAJOR)
    tbl_cat_sub = rs.get_setting_value(setting_csv, sk.KEY_TBL_CAT_SUB)
    tbl_rules = rs.get_setting_value(setting_csv, sk.KEY_TBL_RULES)
    tbl_request = rs.get_setting_value(setting_csv, sk.KEY_TBL_REQUEST)

    # ---- カラム名（setting.csv から取得）----
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

    # ---- SQL（大>中>小>ルール>章）----
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

    rows = cur.execute(sql).fetchall()
    print("rows:", len(rows))

    made_dirs = 0

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

    print("OUT_ROOT      :", out_root)
    print("MANIFEST_PATH :", manifest_path)
    print("mkdir created :", made_dirs)
    print("done")


if __name__ == "__main__":
    main()
