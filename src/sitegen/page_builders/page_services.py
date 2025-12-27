# -*- coding: utf-8 -*-
##
# @file src/sitegen/page_builders/page_services.py
# @brief Generate services page HTML stub.
#
# @if japanese
# サービスページ(services.html)のスタブHTMLを生成します。左ペインにStubカードを配置し、ツリーは読み込みません。
# @endif
#
# @if english
# Generates a stub services page (services.html) with a stub card on the left pane and no tree data.
# @endif
#
from __future__ import annotations

from sitegen.page_builders.common import SiteContext, build_page_html, stub_left_html, write_text


##
# @brief Write services page / サービスページを書き出す
#
# @if japanese
# サービスページのスタブを生成し、左ペインにStubカードを表示してservices.htmlへ保存します。
# @endif
#
# @if english
# Builds the services page stub, shows a stub card on the left pane, and saves to services.html.
# @endif
#
# @param ctx [in]  サイトコンテキスト / Site context

def write(ctx: SiteContext) -> None:
    title = "サービス"
    html = build_page_html(
        site_title=ctx.site_title,
        page_title=title,
        active_nav_id="services",
        build_base_url=ctx.build_base_url,
        has_icon=ctx.has_icon,
        icon_filename=ctx.icon_filename,
        left_header_title=title,
        left_header_sub="Coming soon",
        left_body_html=stub_left_html(title),
        right_breadcrumb=title,
        page_id_for_js="services",
        include_tree_data=False,
        nav_pages=ctx.nav_pages,
    )
    write_text(ctx.out_dir / "services.html", html, ctx.log)