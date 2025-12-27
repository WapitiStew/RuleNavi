# -*- coding: utf-8 -*-
from __future__ import annotations

from sitegen.page_builders.common import SiteContext, build_page_html, write_text


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
        # 将来: cfg_extra={"stubMode": True} などを入れていく想定
    )
    write_text(ctx.out_dir / "index.html", html, ctx.log)
