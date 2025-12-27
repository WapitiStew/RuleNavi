# -*- coding: utf-8 -*-
##
# @file src/sitegen/page_builders/page_wiki.py
# @brief Generate wiki page HTML stub.
#
# @if japanese
# wikiページ(wiki.html)のスタブHTMLを生成します。左ペインにStubカードを配置し、ツリーは読み込みません。
# @endif
#
# @if english
# Generates a stub wiki page (wiki.html) with a stub card on the left pane and no tree data.
# @endif
#
from __future__ import annotations

from sitegen.page_builders.common import SiteContext, build_page_html, stub_left_html, write_text


##
# @brief Write wiki page / wikiページを書き出す
#
# @if japanese
# wikiページのスタブを生成し、左ペインにStubカードを表示してwiki.htmlへ保存します。
# @endif
#
# @if english
# Builds the wiki page stub, shows a stub card on the left pane, and saves to wiki.html.
# @endif
#
# @param ctx [in]  サイトコンテキスト / Site context

def write(ctx: SiteContext) -> None:
    title = "wiki"
    html = build_page_html(
        site_title=ctx.site_title,
        page_title=title,
        active_nav_id="wiki",
        build_base_url=ctx.build_base_url,
        has_icon=ctx.has_icon,
        icon_filename=ctx.icon_filename,
        left_header_title=title,
        left_header_sub="Coming soon",
        left_body_html=stub_left_html(title),
        right_breadcrumb=title,
        page_id_for_js="wiki",
        include_tree_data=False,
        nav_pages=ctx.nav_pages,
    )
    write_text(ctx.out_dir / "wiki.html", html, ctx.log)