# -*- coding: utf-8 -*-
from __future__ import annotations

from sitegen.page_builders.common import SiteContext, build_page_html, write_text


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
