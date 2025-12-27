# -*- coding: utf-8 -*-
##
# @file src/sitegen/page_builders/page_top.py
# @brief Generate TOP page HTML.
#
# @if japanese
# TOPページのスタブHTMLを生成し、index.htmlとして書き出します。
# 左ペインに簡易カードを配置し、ツリー表示は含めません。
# @endif
#
# @if english
# Generates the TOP page stub HTML and writes it as index.html.
# Places a simple card on the left pane and does not include the tree view.
# @endif
#
from __future__ import annotations

from sitegen.page_builders.common import SiteContext, build_page_html, write_text


##
# @brief Write TOP page / TOPページを書き出す
#
# @if japanese
# スタブ用メッセージを左ペインに配置し、TOPページとしてindex.htmlへ保存します。
# @endif
#
# @if english
# Builds a stub message for the left pane and saves it as index.html for the TOP page.
# @endif
#
# @param ctx [in]  サイトコンテキスト / Site context

def write(ctx: SiteContext) -> None:
    left_html = """
<div class="stub-card">
  <h2>TOP</h2>
  <p>ここはTOPページ（ダミー）です。今後、ダッシュボードやショートカットを置けます。</p>
</div>
""".strip()

    html = build_page_html(
        site_title=ctx.site_title,
        page_title="TOP",
        active_nav_id="top",
        build_base_url=ctx.build_base_url,
        has_icon=ctx.has_icon,
        icon_filename=ctx.icon_filename,
        left_header_title="分類ツリー",
        left_header_sub="クリックで本文表示",
        left_body_html=left_html,
        right_breadcrumb="TOP",
        page_id_for_js="top",
        include_tree_data=False,
        nav_pages=ctx.nav_pages,
    )
    write_text(ctx.out_dir / "index.html", html, ctx.log)