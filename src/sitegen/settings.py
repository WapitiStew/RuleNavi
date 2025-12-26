# -*- coding: utf-8 -*-
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

def project_root() -> Path:
    # tools/*.bat は repo root に cd してから実行するので、まず CWD を信用する
    cwd = Path.cwd().resolve()
    if (cwd / "setting.csv").exists():
        return cwd

    # フォールバック：このファイルが src/sitegen/settings.py なら
    # parents[0]=sitegen, parents[1]=src, parents[2]=RuleNavi
    return Path(__file__).resolve().parents[2]


def get_setting(setting_csv: Any, rs: Any, key: str, default: str) -> str:
    try:
        v = rs.get_setting_value(setting_csv, key)
        if v is None:
            return default
        s = str(v).strip()
        return s if s != "" else default
    except Exception:
        return default


def key_or_fallback(sk: Any, name_in_sk: str, fallback: str) -> str:
    if sk and hasattr(sk, name_in_sk):
        return getattr(sk, name_in_sk)
    return fallback


def resolve_build_dir(setting_csv: Any, root: Path, rs: Any, sk: Any) -> Path:
    k = key_or_fallback(sk, "KEY_BUILD_DIR", "BUILD_DIR")
    v = get_setting(setting_csv, rs, k, "build")
    p = Path(v)
    return (root / p).resolve() if not p.is_absolute() else p.resolve()


def resolve_rules_dir(setting_csv: Any, rs: Any, sk: Any) -> str:
    k = key_or_fallback(sk, "KEY_RULES_DIR", "RULES_DIR")
    return get_setting(setting_csv, rs, k, "rules")


def resolve_json_dir(setting_csv: Any, rs: Any, sk: Any) -> str:
    k = key_or_fallback(sk, "KEY_JSON_DIR", "JSON_DIR")
    return get_setting(setting_csv, rs, k, "json")


def resolve_html_dir(setting_csv: Any, rs: Any, sk: Any) -> str:
    k = key_or_fallback(sk, "KEY_HTML_DIR", "HTML_DIR")
    return get_setting(setting_csv, rs, k, "html")


def resolve_tree_json_name(setting_csv: Any, rs: Any, sk: Any) -> str:
    k = key_or_fallback(sk, "KEY_JSON_MAIN_TREE", "JSON_MAIN_TREE")
    return get_setting(setting_csv, rs, k, "tree.json")


def resolve_md_body_filename(setting_csv: Any, rs: Any, sk: Any) -> str:
    k = key_or_fallback(sk, "KEY_MD_BODY_FILENAME", "MD_BODY_FILENAME")
    return get_setting(setting_csv, rs, k, "body.md")


def resolve_site_title(setting_csv: Any, rs: Any, sk: Any) -> str:
    k = key_or_fallback(sk, "KEY_SITE_TITLE", "SITE_TITLE")
    return get_setting(setting_csv, rs, k, "RuleNavi")


def resolve_resource_dir(setting_csv: Any, root: Path, rs: Any, sk: Any) -> Path:
    k = key_or_fallback(sk, "KEY_RESRC_DIR", "RESRC_DIR")
    v = get_setting(setting_csv, rs, k, "resource")
    p = Path(v)
    return (root / p).resolve() if not p.is_absolute() else p.resolve()


def resolve_site_icon_filename(setting_csv: Any, rs: Any, sk: Any) -> str:
    k = key_or_fallback(sk, "KEY_SITE_ICON_FILE", "SITE_ICON_FILE")
    return get_setting(setting_csv, rs, k, "icon.png")


def resolve_tree_json_fullpath(setting_csv: Any, root: Path, build_dir: Path, rs: Any, sk: Any, sh: Any) -> Path:
    name = resolve_tree_json_name(setting_csv, rs, sk)

    # setting_helper があれば優先
    if sh and hasattr(sh, "json_file_fullpath"):
        try:
            p = Path(str(sh.json_file_fullpath(setting_csv, name)))
            return (root / p).resolve() if not p.is_absolute() else p.resolve()
        except Exception:
            pass

    rules_dir = resolve_rules_dir(setting_csv, rs, sk)
    json_dir = resolve_json_dir(setting_csv, rs, sk)
    return (build_dir / rules_dir / json_dir / name).resolve()


def resolve_site_dir(setting_csv: Any, root: Path, build_dir: Path, rs: Any, sk: Any, sh: Any) -> Path:
    # setting_helper があれば優先
    if sh and hasattr(sh, "rule_html_dirpath"):
        try:
            rel = Path(str(sh.rule_html_dirpath(setting_csv)))
            return (root / rel).resolve() if not rel.is_absolute() else rel.resolve()
        except Exception:
            pass

    rules_dir = resolve_rules_dir(setting_csv, rs, sk)
    html_dir = resolve_html_dir(setting_csv, rs, sk)
    return (build_dir / rules_dir / html_dir).resolve()


def compute_build_base_url(site_dir: Path, build_dir: Path) -> str:
    rel = os.path.relpath(build_dir, site_dir).replace("\\", "/")
    if rel == ".":
        return ""
    if not rel.endswith("/"):
        rel += "/"
    return rel
