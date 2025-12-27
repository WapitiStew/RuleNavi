# -*- coding: utf-8 -*-
##
# @file scripts/step2_p05_make_site_stub.py
# @brief Build serverless site stub (HTML/CSS/JS) from generated data.
#
# @if japanese
# tree.json とMarkdownをHTMLへ変換し、静的サイトの土台をbuild/rules/html配下に生成するステップです。
# 設定に基づき出力ディレクトリやサイトタイトル、アイコン等を決定し、アセットやページ、data/tree_data.jsを配置します。
# DBや元データは変更せず、生成物のみを出力します。
# @endif
#
# @if english
# Generates the static site scaffold (HTML/CSS/JS) under build/rules/html using tree.json and Markdown conversions.
# Resolves output directories, site title, and icon from settings, writes assets/pages/tree_data.js, and leaves source data untouched.
# @endif
#
"""
Step2-6: サーバーレス HTML サイトの雛形を構築するスクリプト。
出力先は  build/rules/html/
    index.html              (TOP)
    products.html
    services.html
    rules.html              (一覧表示)
    search.html
    wiki.html
    howto.html
    assets/
      site.css              (共通CSS)
      app.js                (共通JS)
      icon.png              (resource にあればコピー)
    data/
      tree_data.js          (rules 階層ツリーJSONをJS化したもの)

ローカル - file:// で開けるようにfetchを使わず完結。
- 外部へのfetchや環境依存は無し。
- ブラウザのlocalStorageを使い、状態を保持する。
"""

from __future__ import annotations

import argparse  # [JP] 標準: CLI引数処理 / [EN] Standard: CLI argument parsing
from pathlib import Path  # [JP] 標準: パス操作 / [EN] Standard: path utilities

# --- project modules (your repo) ---
try:
    import utility.read_setting as rs  # type: ignore  # [JP] 自作: 設定読込（utility配下） / [EN] Local utility: load settings
except Exception:
    import read_setting as rs  # type: ignore  # [JP] 自作: 設定読込（通常パス） / [EN] Local: fallback settings loader

try:
    import setting_key as sk  # type: ignore  # [JP] 自作: 設定キー定数 / [EN] Local: setting keys
except Exception:
    sk = None  # type: ignore

try:
    import setting_helper as sh  # type: ignore  # [JP] 自作: パス解決ヘルパ / [EN] Local: path helpers
except Exception:
    sh = None  # type: ignore

# --- sitegen (this split) ---
from sitegen.logger import Logger  # [JP] 自作: ロガー / [EN] Local: logger
from sitegen.settings import (
    project_root,  # [JP] 自作: プロジェクトルート解決 / [EN] Local: resolve project root
    resolve_build_dir,  # [JP] 自作: buildディレクトリ解決 / [EN] Local: resolve build dir
    resolve_site_dir,  # [JP] 自作: サイト出力先解決 / [EN] Local: resolve site output dir
    resolve_tree_json_fullpath,  # [JP] 自作: tree.jsonパス解決 / [EN] Local: resolve tree.json path
    resolve_resource_dir,  # [JP] 自作: リソースディレクトリ解決 / [EN] Local: resolve resource dir
    resolve_site_icon_filename,  # [JP] 自作: アイコンファイル名解決 / [EN] Local: resolve icon filename
    resolve_site_title,  # [JP] 自作: サイトタイトル解決 / [EN] Local: resolve site title
    resolve_md_body_filename,  # [JP] 自作: Markdown本文ファイル名解決 / [EN] Local: resolve md body filename
    compute_build_base_url,  # [JP] 自作: base URL計算 / [EN] Local: compute base URL
)
from sitegen.data import (
    load_tree_json,  # [JP] 自作: tree.json読込 / [EN] Local: load tree.json
    mark_and_collect_md_targets,  # [JP] 自作: MD変換対象の抽出 / [EN] Local: collect md targets
    convert_md_targets_to_html,  # [JP] 自作: MDをHTMLへ変換 / [EN] Local: convert md to html
    write_tree_data_js,  # [JP] 自作: tree_data.js出力 / [EN] Local: write tree_data.js
)
from sitegen.assets import (
    write_assets,  # [JP] 自作: CSS/JS出力 / [EN] Local: write assets
    copy_icon_if_exists,  # [JP] 自作: アイコンコピー / [EN] Local: copy icon if exists
)
from sitegen.pages import (
    NAV_PAGES,  # [JP] 自作: ナビゲーション定義 / [EN] Local: navigation definition
    write_all_pages,  # [JP] 自作: HTMLページ生成 / [EN] Local: generate HTML pages
)


##
# @brief Main entry to build static site / 静的サイト生成のメイン処理
#
# @if japanese
# CLI引数で出力先やログ詳細度を受け取り、設定ファイルを読み込んでbuild先/サイト先を解決します。
# tree.jsonを読み込みMDをHTMLに変換し、data/js/assets/pagesを出力してインデックスHTMLを生成します。
# アイコンのコピーやbase URL計算も行い、完了後にindex.htmlのパスをログ表示します。
# @endif
#
# @if english
# Parses CLI args for output directory and verbosity, loads settings, resolves build/site paths, and reads tree.json.
# Converts Markdown to HTML, writes data/js/assets/pages, computes the base URL, and copies the site icon when available.
# Logs target directories and the resulting index.html path upon completion.
# @endif
#
# @details
# @if japanese
# - 設定読込後、build/siteディレクトリを決定する。
# - tree.jsonを読み込み、MDターゲットを抽出してHTMLへ変換する。
# - dataディレクトリへtree_data.jsを出力し、assetsとページHTMLを生成する。
# - アイコンのコピーとbase URL算出を行い、最後に出力先をログ表示する。
# @endif
# @if english
# - After loading settings, determine build/site directories.
# - Load tree.json, collect Markdown targets, and convert them to HTML.
# - Output tree_data.js to the data directory and generate assets plus HTML pages.
# - Copy icon if present, compute base URL, and log the output location.
# @endif
#
# @return int  終了コード / Exit code
def main() -> int:
    parser = argparse.ArgumentParser(description="Step2-6: build serverless site (split version).")
    parser.add_argument("--quiet", action="store_true", help="less logs (default: verbose)")
    parser.add_argument(
        "--out-dir", type=str, default="", help="override output dir (default: build/rules/html)"
    )
    args = parser.parse_args()

    log = Logger(verbose=(not args.quiet))

    # ------------------------------------------------------------
    # 設定読込と出力パス解決 / Load settings and resolve output paths
    # ------------------------------------------------------------
    setting_csv = rs.load_setting_csv()
    root = project_root()
    build_dir = resolve_build_dir(setting_csv, root, rs, sk)
    site_dir = (
        Path(args.out_dir).resolve()
        if args.out_dir
        else resolve_site_dir(setting_csv, root, build_dir, rs, sk, sh)
    )

    site_dir.mkdir(parents=True, exist_ok=True)
    log.info(f"project_root : {root}")
    log.info(f"build_dir     : {build_dir}")
    log.info(f"site_dir      : {site_dir}")

    build_base_url = compute_build_base_url(site_dir, build_dir)
    log.info(f"buildBaseUrl  : '{build_base_url}'")

    # ------------------------------------------------------------
    # tree.json 読み込み / Load tree.json
    # ------------------------------------------------------------
    tree_json = resolve_tree_json_fullpath(setting_csv, root, build_dir, rs, sk, sh)
    if not tree_json.exists():
        raise FileNotFoundError(f"tree.json not found: {tree_json}")

    tree = load_tree_json(tree_json, log)

    # ------------------------------------------------------------
    # MD -> body.html へ変換 / Convert Markdown to HTML
    # ------------------------------------------------------------
    md_name = resolve_md_body_filename(setting_csv, rs, sk)
    count_nodes, targets = mark_and_collect_md_targets(tree, build_dir, md_name, log)
    log.info(f"tree nodes    : {count_nodes}")
    log.info(f"md targets    : {len(targets)}")

    convert_md_targets_to_html(targets, log)

    # ------------------------------------------------------------
    # data 出力 (file://対応用のJS) / Output data (JS for file://)
    # ------------------------------------------------------------
    data_dir = site_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    write_tree_data_js(data_dir, tree, log)

    # ------------------------------------------------------------
    # assets 出力 (CSS/JS/Icon) / Output assets
    # ------------------------------------------------------------
    assets_dir = site_dir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)

    write_assets(assets_dir, log)

    # icon.png のコピー（存在すれば） / Copy icon.png if present
    res_dir = resolve_resource_dir(setting_csv, root, rs, sk)
    icon_name = resolve_site_icon_filename(setting_csv, rs, sk)
    has_icon = copy_icon_if_exists(res_dir, icon_name, assets_dir, log)

    # ------------------------------------------------------------
    # ページ生成 (index, rules など) / Generate pages
    # ------------------------------------------------------------
    site_title = resolve_site_title(setting_csv, rs, sk)
    write_all_pages(
        out_dir=site_dir,
        site_title=site_title,
        build_base_url=build_base_url,
        has_icon=has_icon,
        icon_filename=icon_name,
        nav_pages=NAV_PAGES,
        log=log,
    )

    log.info("DONE. open:")
    log.info(str((site_dir / "index.html").resolve()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
