# -*- coding: utf-8 -*-
import argparse, csv, re, sqlite3
from pathlib import Path

import setting_key as sk
import read_setting as rs
import setting_helper as sh

DEFAULT_MANIFEST = "manifest_rule_cap.tsv"
DEFAULT_MD = "body.md"
KEY_TSV_MANIFEST_RULE_CAP = "TSV_MANIFEST_RULE_CAP"   # optional in setting.csv
KEY_MD_BODY_FILENAME     = "MD_BODY_FILENAME"         # optional in setting.csv


def safe_seg(s: str) -> str:
    s = (s or "").strip()
    s = re.sub(r'[\\/:*?"<>|]+', "_", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s or "_"


def gs(setting_csv, key, default):
    try:
        v = rs.get_setting_value(setting_csv, key)
        return str(v) if v is not None else default
    except Exception:
        return default


def norm(v):
    if v is None:
        return ""
    return str(v).replace("\r\n", "\n").replace("\r", "\n").strip()


def tree_lines(nodes):
    out = []
    def walk(items, prefix):
        last = len(items) - 1
        for i, n in enumerate(items):
            is_last = (i == last)
            out.append(prefix + ("└ " if is_last else "├ ") + n["label"])
            ch = n.get("children") or []
            if ch:
                walk(ch, prefix + ("  " if is_last else "│ "))
    walk(nodes, "")
    return out


def resolve_db(setting_csv) -> Path:
    raw = str(rs.get_setting_value(setting_csv, sk.KEY_DB_NAME)).strip()
    if ("/" in raw) or ("\\" in raw):
        return Path(raw)
    return Path(sh.rules_file_fullpath(setting_csv, raw))


def load_manifest(setting_csv):
    out_root = Path(sh.rules_file_dir_path(setting_csv))
    manifest = gs(setting_csv, KEY_TSV_MANIFEST_RULE_CAP, DEFAULT_MANIFEST)
    path = out_root / manifest
    if not path.exists():
        raise FileNotFoundError(f"manifest not found: {path}")

    req = {"type_path","major_path","sub_path","id_rule","key_rule","id_cap","out_dir"}
    rules = {}

    with path.open("r", encoding="utf-8", newline="") as f:
        r = csv.DictReader(f, delimiter="\t")
        if r.fieldnames is None or not req.issubset(set(r.fieldnames)):
            raise ValueError(f"manifest header mismatch: {r.fieldnames}")

        for row in r:
            id_rule = (row.get("id_rule") or "").strip()
            if not id_rule:
                continue
            id_cap = (row.get("id_cap") or "").strip()
            out_dir = Path((row.get("out_dir") or "").strip())
            if not str(out_dir):
                continue

            rule_dir = out_dir if id_cap == "" else out_dir.parent
            key = str(rule_dir)

            if key not in rules:
                rules[key] = {
                    "type": (row.get("type_path") or "").strip(),
                    "maj":  (row.get("major_path") or "").strip(),
                    "sub":  (row.get("sub_path") or "").strip(),
                    "id_rule": id_rule,
                    "key_rule": (row.get("key_rule") or "").strip(),
                    "rule_dir": rule_dir,
                    "caps": []
                }

            if id_cap and all(c["id_cap"] != id_cap for c in rules[key]["caps"]):
                rules[key]["caps"].append({"id_cap": id_cap, "cap_dir": out_dir})

    lst = list(rules.values())
    lst.sort(key=lambda x: (x["type"], x["maj"], x["sub"], x["id_rule"]))
    for x in lst:
        x["caps"].sort(key=lambda c: c["id_cap"])
    return lst, out_root


def write_or_check(path: Path, content: str, overwrite: bool, check_only: bool):
    try:
        existed = path.exists()
        if check_only:
            return ("OK","exists") if existed else ("NG","missing")
        path.parent.mkdir(parents=True, exist_ok=True)
        if existed and (not overwrite):
            return ("OK","exists")
        path.write_text(content, encoding="utf-8")
        return ("OK","updated" if existed else "created") if path.exists() else ("NG","failed")
    except Exception as e:
        return ("NG", f"failed({type(e).__name__})")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--overwrite", action="store_true", help="既存body.mdも上書き")
    ap.add_argument("--check-only", action="store_true", help="書き込みせず存在チェックのみ")
    a = ap.parse_args()

    setting_csv = rs.load_setting_csv()
    db = resolve_db(setting_csv)
    if not db.exists():
        print(f"[Error] DB not found: {db}")
        return 2

    try:
        rules, out_root = load_manifest(setting_csv)
    except Exception as e:
        print(f"[Error] {e}")
        return 2

    md_name = (gs(setting_csv, KEY_MD_BODY_FILENAME, DEFAULT_MD).strip() or DEFAULT_MD)

    # tables / columns (setting.csv 依存)
    tbl_rules   = str(rs.get_setting_value(setting_csv, sk.KEY_TBL_RULES))
    tbl_request = str(rs.get_setting_value(setting_csv, sk.KEY_TBL_REQUEST))

    c_rules_pkey   = str(rs.get_setting_value(setting_csv, sk.KEY_ITM_RULES_PKEY))
    c_rules_id     = str(rs.get_setting_value(setting_csv, sk.KEY_ITM_RULES_ID_RULE))
    c_rules_name   = str(rs.get_setting_value(setting_csv, sk.KEY_ITM_RULES_NAME_RULE))
    c_rules_link   = str(rs.get_setting_value(setting_csv, sk.KEY_ITM_RULES_LINK))
    c_rules_cr     = str(rs.get_setting_value(setting_csv, sk.KEY_ITM_RULES_CREATED_DATE))
    c_rules_up     = str(rs.get_setting_value(setting_csv, sk.KEY_ITM_RULES_UPDATE_DATE))

    c_req_pkey     = str(rs.get_setting_value(setting_csv, sk.KEY_ITM_REQUEST_PKEY))
    c_req_key_rule = str(rs.get_setting_value(setting_csv, sk.KEY_ITM_REQUEST_KEY_RULE))
    c_req_id_cap   = str(rs.get_setting_value(setting_csv, sk.KEY_ITM_REQUEST_ID_CAP))
    c_req_cap_tit  = str(rs.get_setting_value(setting_csv, sk.KEY_ITM_REQUEST_FTITLE_CAPTER))
    c_req_sec_tit  = str(rs.get_setting_value(setting_csv, sk.KEY_ITM_REQUEST_TITLE_SECTION))
    c_req_top      = str(rs.get_setting_value(setting_csv, sk.KEY_ITM_REQUEST_FTOP_BODY))
    c_req_low      = str(rs.get_setting_value(setting_csv, sk.KEY_ITM_REQUEST_LOW_BODY))
    c_req_ref      = str(rs.get_setting_value(setting_csv, sk.KEY_ITM_REQUEST_REFERENCE))

    ok = ng = 0

    with sqlite3.connect(db) as con:
        con.row_factory = sqlite3.Row

        sql_rule = f"SELECT {c_rules_id} AS id_rule,{c_rules_name} AS name_rule,{c_rules_link} AS link,{c_rules_cr} AS created_date,{c_rules_up} AS update_date FROM {tbl_rules} WHERE {c_rules_pkey}=?"
        sql_cap_title = f"SELECT {c_req_cap_tit} AS title_capter FROM {tbl_request} WHERE {c_req_key_rule}=? AND {c_req_id_cap}=? AND {c_req_cap_tit} IS NOT NULL LIMIT 1"
        sql_cap_rows = f"SELECT {c_req_pkey} AS key_req,{c_req_cap_tit} AS title_capter,{c_req_sec_tit} AS title_section,{c_req_top} AS top_body,{c_req_low} AS low_body,{c_req_ref} AS reference FROM {tbl_request} WHERE {c_req_key_rule}=? AND {c_req_id_cap}=? ORDER BY {c_req_pkey}"

        for r in rules:
            key_rule = r["key_rule"]
            meta_row = con.execute(sql_rule, (key_rule,)).fetchone()
            meta = dict(meta_row) if meta_row else {}

            cap_titles = {}
            for c in r["caps"]:
                row = con.execute(sql_cap_title, (key_rule, c["id_cap"])).fetchone()
                cap_titles[c["id_cap"]] = norm(row["title_capter"]) if row else ""

            title = f'{r["id_rule"]} {norm(meta.get("name_rule"))}'.strip()
            lines = [f"# {title}", "", f"- key_rule: {key_rule}"]
            if norm(meta.get("link")):         lines.append(f"- link: {norm(meta.get('link'))}")
            if norm(meta.get("created_date")): lines.append(f"- created: {norm(meta.get('created_date'))}")
            if norm(meta.get("update_date")):  lines.append(f"- updated: {norm(meta.get('update_date'))}")
            lines.append("")

            if r["caps"]:
                lines += ["## Chapters", ""]
                for c in r["caps"]:
                    id_cap = c["id_cap"]
                    lines.append(f"- [{id_cap}] {cap_titles.get(id_cap,'')}".strip() + f"  (./{safe_seg(id_cap)}/{md_name})")
                lines.append("")
            else:
                lines += ["> (no chapters)", ""]

            rule_md = "\n".join(lines).rstrip() + "\n"
            rule_md_path = Path(r["rule_dir"]) / md_name
            st, act = write_or_check(rule_md_path, rule_md, a.overwrite, a.check_only)
            r["md_path"], r["st"], r["act"] = rule_md_path, st, act
            ok += (st == "OK"); ng += (st != "OK")

            for c in r["caps"]:
                id_cap = c["id_cap"]
                cap_md_path = Path(c["cap_dir"]) / md_name
                rows = con.execute(sql_cap_rows, (key_rule, id_cap)).fetchall()

                cap_t = ""
                for row in rows:
                    t = norm(row["title_capter"])
                    if t: cap_t = t; break

                cap_lines = [f"# {id_cap} {cap_t}".strip(), "", f'- id_rule: {r["id_rule"]}', f"- key_rule: {key_rule}", ""]
                if not rows:
                    cap_lines += ["> (no sections)", ""]
                else:
                    for row in rows:
                        sec = norm(row["title_section"])
                        if sec: cap_lines += [f"## {sec}", ""]
                        body = "\n\n".join([p for p in [norm(row["top_body"]), norm(row["low_body"])] if p])
                        if body: cap_lines += [body, ""]
                        ref = norm(row["reference"])
                        if ref: cap_lines += [f"- reference: {ref}", ""]

                cap_md = "\n".join(cap_lines).rstrip() + "\n"
                cst, cact = write_or_check(cap_md_path, cap_md, a.overwrite, a.check_only)
                c["md_path"], c["st"], c["act"] = cap_md_path, cst, cact
                ok += (cst == "OK"); ng += (cst != "OK")

    print("\n=== Step2-5 Markdown Export Check ===")
    print(f"DB      : {db.as_posix()}")
    print(f"OUT_ROOT: {out_root.as_posix()}")
    print(f"MD_NAME : {md_name}\n")
    print(out_root.as_posix())

    nodes = []
    for r in rules:
        kids = [{"label": f'{c["md_path"].as_posix()} ({c["act"]}): {c["st"]}', "children": []} for c in r["caps"]]
        nodes.append({"label": f'{r["md_path"].as_posix()} ({r["act"]}): {r["st"]}', "children": kids})

    for line in tree_lines(nodes):
        print(line)

    print(f"\nSummary: OK={ok}, NG={ng}")
    return 0 if ng == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
