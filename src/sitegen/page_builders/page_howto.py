# -*- coding: utf-8 -*-
from __future__ import annotations

from sitegen.page_builders.common import SiteContext, build_page_html, stub_left_html, write_text


def write(ctx: SiteContext) -> None:
    title = "製品"
    html = build_page_html(
        site_title=ctx.site_title,
        page_title=title,
        active_nav_id="products",
        build_base_url=ctx.build_base_url,
        has_icon=ctx.has_icon,
        icon_filename=ctx.icon_filename,
        left_header_title=title,
        left_header_sub="Coming soon",
        left_body_html=stub_left_html(title),
        right_breadcrumb=title,
        page_id_for_js="products",
        include_tree_data=False,
        nav_pages=ctx.nav_pages,
    )
    write_text(ctx.out_dir / "products.html", html, ctx.log)
