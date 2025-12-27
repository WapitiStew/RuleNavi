# -*- coding: utf-8 -*-
"""
Step2-6: サーバーレス HTML サイト生成（分割版）

出力（既定）
  build/rules/html/
    index.html              (TOP)
    products.html
    services.html
    rules.html              (基準一覧)
    search.html
    wiki.html
    howto.html
    assets/
      site.css              (共通CSS)
      app.js                (共通JS)
      icon.png              (resource にあればコピー)
    data/
      tree_data.js          (rules 用：ツリーデータ埋め込み)

ポイント
- file:// 直開きでも動く（fetchを使わない）
- 右ペインのスクロールは親側で統一（iframeは高さ追従）
- 左ペインはドラッグで幅変更 + localStorage 保存
- ツリー展開状態は localStorage で維持（TOPへ戻っても維持）
"""

from __future__ import annotations

import argparse
from pathlib import Path

# --- project modules (your repo) ---
try:
    import utility.read_setting as rs  # type: ignore
except Exception:
    import read_setting as rs  # type: ignore

try:
    import setting_key as sk  # type: ignore
except Exception:
    sk = None  # type: ignore

try:
    import setting_helper as sh  # type: ignore
except Exception:
    sh = None  # type: ignore

# --- sitegen (this split) ---
from sitegen.logger import Logger
from sitegen.settings import (
    project_root,
    resolve_build_dir,
    resolve_site_dir,
    resolve_tree_json_fullpath,
    resolve_resource_dir,
    resolve_site_icon_filename,
    resolve_site_title,
    resolve_md_body_filename,
    compute_build_base_url,
)
from sitegen.data import (
    load_tree_json,
    mark_and_collect_md_targets,
    convert_md_targets_to_html,
    write_tree_data_js,
)
from sitegen.assets import (
    write_assets,
    copy_icon_if_exists,
)
from sitegen.pages import (
    NAV_PAGES,
    write_all_pages,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Step2-6: build serverless site (split version).")
    parser.add_argument("--quiet", action="store_true", help="less logs (default: verbose)")
    parser.add_argument(
        "--out-dir", type=str, default="", help="override output dir (default: build/rules/html)"
    )
    args = parser.parse_args()

    log = Logger(verbose=(not args.quiet))

    # ------------------------------------------------------------
    # 設定読み込み
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
    # tree.json 読み込み
    # ------------------------------------------------------------
    tree_json = resolve_tree_json_fullpath(setting_csv, root, build_dir, rs, sk, sh)
    if not tree_json.exists():
        raise FileNotFoundError(f"tree.json not found: {tree_json}")

    tree = load_tree_json(tree_json, log)

    # ------------------------------------------------------------
    # MD -> body.html 変換（iframeで表示するため）
    # ------------------------------------------------------------
    md_name = resolve_md_body_filename(setting_csv, rs, sk)
    count_nodes, targets = mark_and_collect_md_targets(tree, build_dir, md_name, log)
    log.info(f"tree nodes    : {count_nodes}")
    log.info(f"md targets    : {len(targets)}")

    convert_md_targets_to_html(targets, log)

    # ------------------------------------------------------------
    # data 出力（file://対応のため fetch せず JS に埋め込み）
    # ------------------------------------------------------------
    data_dir = site_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    write_tree_data_js(data_dir, tree, log)

    # ------------------------------------------------------------
    # assets 出力（共通CSS/JS）
    # ------------------------------------------------------------
    assets_dir = site_dir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)

    write_assets(assets_dir, log)

    # icon.png のコピー（resource/icon.png がなければデフォルト表示）
    res_dir = resolve_resource_dir(setting_csv, root, rs, sk)
    icon_name = resolve_site_icon_filename(setting_csv, rs, sk)
    has_icon = copy_icon_if_exists(res_dir, icon_name, assets_dir, log)

    # ------------------------------------------------------------
    # pages 出力（index=TOP / rules=基準一覧）
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
