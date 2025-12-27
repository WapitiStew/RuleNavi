# -*- coding: utf-8 -*-
##
# @file src/sitegen/settings.py
# @brief Resolve paths and settings for site generation.
#
# @if japanese
# setting.csvや補助モジュール(setting_helper, setting_key)の値を元に、ビルド/リソース/JSON/HTMLなどのパスやファイル名を解決します。
# 文字列処理のみで状態変更は行わず、フォールバック値を持たせて頑健性を確保します。
# @endif
#
# @if english
# Resolves build/resource/JSON/HTML paths and filenames based on setting.csv values and helper modules.
# Pure string/path handling with sensible fallbacks to remain robust without altering external state.
# @endif
#

from __future__ import annotations

import os  # [JP] 標準: 相対パス計算 / [EN] Standard: path relativity
from pathlib import Path  # [JP] 標準: パス操作 / [EN] Standard: path utilities
from typing import Any  # [JP] 標準: 任意型ヒント / [EN] Standard: Any type hint


##
# @brief Resolve project root / プロジェクトルートを解決する
#
# @if japanese
# CWDにsetting.csvがあればそこをルートとし、無い場合はこのファイルの親ディレクトリからRuleNaviルートを推定します。
# tools/*.batがCWDを変更する前提に対応します。
# @endif
#
# @if english
# Returns CWD when setting.csv exists; otherwise infers the RuleNavi root from this file's ancestors.
# Supports cases where tools/*.bat adjusts CWD.
# @endif
#
# @return Path  ルートパス / Resolved root path
def project_root() -> Path:
    # tools/*.bat は repo root に cd してから呼ばれる前提なので、まずCWDを優先
    cwd = Path.cwd().resolve()
    if (cwd / "setting.csv").exists():
        return cwd

    # スクリプト位置から遡って RuleNavi ルートを特定（parents[2]）
    return Path(__file__).resolve().parents[2]


##
# @brief Get setting value with default / 設定値を取得しデフォルトを適用
#
# @if japanese
# rs.get_setting_valueを使いキーを取得し、Noneや空文字の場合はdefaultを返します。例外時もdefaultを返します。
# @endif
#
# @if english
# Retrieves a setting via rs.get_setting_value; returns default on None/empty/exception.
# @endif
#
# @param setting_csv [in]  設定DataFrame / Settings data
# @param rs [in]  read_settingモジュール / read_setting module
# @param key [in]  キー名 / Key name
# @param default [in]  フォールバック値 / Fallback value
# @return str  取得値またはデフォルト / Retrieved value or default
def get_setting(setting_csv: Any, rs: Any, key: str, default: str) -> str:
    try:
        v = rs.get_setting_value(setting_csv, key)
        if v is None:
            return default
        s = str(v).strip()
        return s if s != "" else default
    except Exception:
        return default


##
# @brief Prefer setting_key constant when available / setting_keyの定数を優先取得
#
# @if japanese
# skに指定名の属性が存在すればそれを返し、なければフォールバック文字列を返します。
# @endif
#
# @if english
# Returns the attribute from sk when present; otherwise returns the fallback string.
# @endif
#
# @param sk [in]  setting_keyモジュール / setting_key module
# @param name_in_sk [in]  属性名 / Attribute name
# @param fallback [in]  フォールバック文字列 / Fallback string
# @return str  取得したキー名 / Selected key name
def key_or_fallback(sk: Any, name_in_sk: str, fallback: str) -> str:
    if sk and hasattr(sk, name_in_sk):
        return getattr(sk, name_in_sk)
    return fallback


##
# @brief Resolve build directory path / ビルドディレクトリを解決する
#
# @if japanese
# KEY_BUILD_DIRを取得し、絶対パスならそのまま、相対ならroot基準で解決します。
# @endif
#
# @if english
# Resolves KEY_BUILD_DIR to an absolute path using root when relative.
# @endif
#
# @param setting_csv [in]  設定DataFrame / Settings data
# @param root [in]  ルートパス / Project root
# @param rs [in]  read_settingモジュール / read_setting module
# @param sk [in]  setting_keyモジュール / setting_key module
# @return Path  ビルドディレクトリ / Build directory
def resolve_build_dir(setting_csv: Any, root: Path, rs: Any, sk: Any) -> Path:
    k = key_or_fallback(sk, "KEY_BUILD_DIR", "BUILD_DIR")
    v = get_setting(setting_csv, rs, k, "build")
    p = Path(v)
    return (root / p).resolve() if not p.is_absolute() else p.resolve()


##
# @brief Resolve rules directory name / ルールディレクトリ名を解決する
def resolve_rules_dir(setting_csv: Any, rs: Any, sk: Any) -> str:
    k = key_or_fallback(sk, "KEY_RULES_DIR", "RULES_DIR")
    return get_setting(setting_csv, rs, k, "rules")


##
# @brief Resolve JSON directory name / JSONディレクトリ名を解決する
def resolve_json_dir(setting_csv: Any, rs: Any, sk: Any) -> str:
    k = key_or_fallback(sk, "KEY_JSON_DIR", "JSON_DIR")
    return get_setting(setting_csv, rs, k, "json")


##
# @brief Resolve HTML directory name / HTMLディレクトリ名を解決する
def resolve_html_dir(setting_csv: Any, rs: Any, sk: Any) -> str:
    k = key_or_fallback(sk, "KEY_HTML_DIR", "HTML_DIR")
    return get_setting(setting_csv, rs, k, "html")


##
# @brief Resolve tree.json filename / tree.jsonのファイル名を解決する
def resolve_tree_json_name(setting_csv: Any, rs: Any, sk: Any) -> str:
    k = key_or_fallback(sk, "KEY_JSON_MAIN_TREE", "JSON_MAIN_TREE")
    return get_setting(setting_csv, rs, k, "tree.json")


##
# @brief Resolve Markdown body filename / Markdown本文ファイル名を解決する
def resolve_md_body_filename(setting_csv: Any, rs: Any, sk: Any) -> str:
    k = key_or_fallback(sk, "KEY_MD_BODY_FILENAME", "MD_BODY_FILENAME")
    return get_setting(setting_csv, rs, k, "body.md")


##
# @brief Resolve site title / サイトタイトルを解決する
def resolve_site_title(setting_csv: Any, rs: Any, sk: Any) -> str:
    k = key_or_fallback(sk, "KEY_SITE_TITLE", "SITE_TITLE")
    return get_setting(setting_csv, rs, k, "RuleNavi")


##
# @brief Resolve resource directory path / リソースディレクトリを解決する
#
# @if japanese
# KEY_RESRC_DIRを取得し、相対パスならroot基準で解決します。
# @endif
#
# @if english
# Resolves KEY_RESRC_DIR, making it absolute using root when relative.
# @endif
#
# @return Path  リソースディレクトリ / Resource directory
def resolve_resource_dir(setting_csv: Any, root: Path, rs: Any, sk: Any) -> Path:
    k = key_or_fallback(sk, "KEY_RESRC_DIR", "RESRC_DIR")
    v = get_setting(setting_csv, rs, k, "resource")
    p = Path(v)
    return (root / p).resolve() if not p.is_absolute() else p.resolve()


##
# @brief Resolve site icon filename / サイトアイコンのファイル名を解決する
def resolve_site_icon_filename(setting_csv: Any, rs: Any, sk: Any) -> str:
    k = key_or_fallback(sk, "KEY_SITE_ICON_FILE", "SITE_ICON_FILE")
    return get_setting(setting_csv, rs, k, "icon.png")


##
# @brief Resolve full path to tree.json / tree.jsonのフルパスを解決する
#
# @if japanese
# setting_helperが利用可能ならjson_file_fullpathを試し、失敗時はbuild_dir/rules/json配下で組み立てます。
# @endif
#
# @if english
# Attempts sh.json_file_fullpath when available; otherwise builds path under build_dir/rules/json.
# @endif
#
# @param setting_csv [in]  設定DataFrame / Settings data
# @param root [in]  ルートパス / Project root
# @param build_dir [in]  ビルドディレクトリ / Build directory
# @param rs [in]  read_settingモジュール / read_setting module
# @param sk [in]  setting_keyモジュール / setting_key module
# @param sh [in]  setting_helperモジュール / setting_helper module
# @return Path  tree.jsonフルパス / Full path to tree.json
def resolve_tree_json_fullpath(
    setting_csv: Any, root: Path, build_dir: Path, rs: Any, sk: Any, sh: Any
) -> Path:
    name = resolve_tree_json_name(setting_csv, rs, sk)

    # setting_helper があれば優先的に利用して解決
    if sh and hasattr(sh, "json_file_fullpath"):
        try:
            p = Path(str(sh.json_file_fullpath(setting_csv, name)))
            return (root / p).resolve() if not p.is_absolute() else p.resolve()
        except Exception:
            pass

    rules_dir = resolve_rules_dir(setting_csv, rs, sk)
    json_dir = resolve_json_dir(setting_csv, rs, sk)
    return (build_dir / rules_dir / json_dir / name).resolve()


##
# @brief Resolve site output directory / サイト出力ディレクトリを解決する
#
# @if japanese
# setting_helperのrule_html_dirpathがあればそれを優先し、無ければbuild/rules/htmlで組み立てます。
# @endif
#
# @if english
# Prefers sh.rule_html_dirpath when available; otherwise builds under build/rules/html.
# @endif
#
# @return Path  サイト出力パス / Site output path
def resolve_site_dir(
    setting_csv: Any, root: Path, build_dir: Path, rs: Any, sk: Any, sh: Any
) -> Path:
    # setting_helper があれば利用
    if sh and hasattr(sh, "rule_html_dirpath"):
        try:
            rel = Path(str(sh.rule_html_dirpath(setting_csv)))
            return (root / rel).resolve() if not rel.is_absolute() else rel.resolve()
        except Exception:
            pass

    rules_dir = resolve_rules_dir(setting_csv, rs, sk)
    html_dir = resolve_html_dir(setting_csv, rs, sk)
    return (build_dir / rules_dir / html_dir).resolve()


##
# @brief Compute buildBaseUrl relative path / buildBaseUrlを計算する
#
# @if japanese
# site_dirからbuild_dirへの相対パスを計算し、末尾にスラッシュを付けて返します。同一ディレクトリなら空文字を返します。
# @endif
#
# @if english
# Computes relative path from site_dir to build_dir, appending a trailing slash; returns empty string when in the same directory.
# @endif
#
# @param site_dir [in]  サイト出力ディレクトリ / Site output directory
# @param build_dir [in]  ビルドディレクトリ / Build directory
# @return str  buildBaseUrl文字列 / buildBaseUrl string
def compute_build_base_url(site_dir: Path, build_dir: Path) -> str:
    rel = os.path.relpath(build_dir, site_dir).replace("\\", "/")
    if rel == ".":
        return ""
    if not rel.endswith("/"):
        rel += "/"
    return rel
