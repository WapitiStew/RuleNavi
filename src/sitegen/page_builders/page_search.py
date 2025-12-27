# -*- coding: utf-8 -*-
##
# @file src/sitegen/page_builders/page_search.py
# @brief Generate search page HTML stub.
#
# @if japanese
# 検索ページ(search.html)のスタブHTMLを生成します。左ペインにStubカードを配置し、ツリーは読み込みません。
# @endif
#
# @if english
# Generates a stub search page (search.html) with a stub card on the left pane and no tree data.
# @endif
#
from __future__ import annotations

from sitegen.page_builders.common import SiteContext, build_page_html, stub_left_html, write_text


##
# @brief Write search page / 検索ページを書き出す
#
# @if japanese
# 検索ページのスタブを生成し、左ペインにStubカードを表示してsearch.htmlへ保存します。
# @endif
#
# @if english
# Builds the search page stub, shows a stub card on the left pane, and saves to search.html.
# @endif
#
# @param ctx [in]  サイトコンテキスト / Site context

def write(ctx: SiteContext) -> None:
    title = "検索"
    html = build_page_html(
        site_title=ctx.site_title,
        page_title=title,
        active_nav_id="search",
        build_base_url=ctx.build_base_url,
        has_icon=ctx.has_icon,
        icon_filename=ctx.icon_filename,
        left_header_title=title,
        left_header_sub="Coming soon",
        left_body_html=stub_left_html(title),
        right_breadcrumb=title,
        page_id_for_js="search",
        include_tree_data=False,
        nav_pages=ctx.nav_pages,
    )
    write_text(ctx.out_dir / "search.html", html, ctx.log)