# -*- coding: utf-8 -*-
##
# @file src/sitegen/page_builders/page_rules.py
# @brief Generate rules listing page HTML.
#
# @if japanese
# ルール一覧ページ(rules.html)のHTMLを生成します。左ペインにはツリー表示のプレースホルダを配置し、tree_data.jsを読み込みます。
# @endif
#
# @if english
# Generates the rules listing page (rules.html). Places a placeholder for the tree view on the left pane and loads tree_data.js.
# @endif
#
from __future__ import annotations

from sitegen.page_builders.common import SiteContext, build_page_html, write_text


##
# @brief Write rules page / ルール一覧ページを書き出す
#
# @if japanese
# rules.htmlを生成し、左ペインにツリー描画用のプレースホルダを配置します。
# @endif
#
# @if english
# Writes rules.html and places a placeholder for the tree rendering on the left pane.
# @endif
#
# @param ctx [in]  サイトコンテキスト / Site context

def write(ctx: SiteContext) -> None:
    rules_left = "<!-- rules tree will be rendered by app.js -->"

    html = build_page_html(
        site_title=ctx.site_title,
        page_title="基準一覧",
        active_nav_id="rules",
        build_base_url=ctx.build_base_url,
        has_icon=ctx.has_icon,
        icon_filename=ctx.icon_filename,
        left_header_title="分類ツリー",
        left_header_sub="クリックで本文表示",
        left_body_html=rules_left,
        right_breadcrumb="ready",
        page_id_for_js="rules",
        include_tree_data=True,
        nav_pages=ctx.nav_pages,
    )
    write_text(ctx.out_dir / "rules.html", html, ctx.log)