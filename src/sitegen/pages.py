# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
from typing import List, Tuple

from sitegen.logger import Logger

# (page_id, label, filename)
NAV_PAGES: List[Tuple[str, str, str]] = [
    ("top", "TOP", "index.html"),
    ("products", "製品", "products.html"),
    ("services", "サービス", "services.html"),
    ("rules", "基準一覧", "rules.html"),
    ("search", "検索", "search.html"),
    ("wiki", "wiki", "wiki.html"),
    ("howto", "How to", "howto.html"),
]


def build_nav_html(active_id: str, nav_pages: List[Tuple[str, str, str]]) -> str:
    parts: List[str] = []
    for pid, label, href in nav_pages:
        cls = "tab is-active" if pid == active_id else "tab"
        parts.append(f'<a class="{cls}" href="./{href}" data-nav="{pid}">{label}</a>')
    return "\n".join(parts)


def build_page_html(
    *,
    site_title: str,
    page_title: str,
    active_nav_id: str,
    build_base_url: str,
    has_icon: bool,
    icon_filename: str,
    left_header_title: str,
    left_header_sub: str,
    left_body_html: str,
    right_breadcrumb: str,
    page_id_for_js: str,
    include_tree_data: bool,
    nav_pages: List[Tuple[str, str, str]],
) -> str:
    icon_html = (
        f'<img class="icon-img" src="./assets/{icon_filename}" alt="icon" />'
        if has_icon
        else '<div class="icon-emoji">🦌</div>'
    )
    nav_html = build_nav_html(active_nav_id, nav_pages)

    tree_script = '<script src="./data/tree_data.js"></script>' if include_tree_data else ""

    return f"""<!doctype html>
<html lang="ja">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{page_title} - {site_title}</title>
  <link rel="stylesheet" href="./assets/site.css" />
</head>
<body>
  <header class="topbar">
    <div style="display:flex; align-items:center; gap:10px; min-width:0;">
      <button class="brand" id="brandHome" title="Home">
        {icon_html}
        <div class="title">{site_title}</div>
      </button>
      <nav class="nav" aria-label="site nav">
{nav_html}
      </nav>
    </div>
    <div></div>
    <div class="search">
      <div>🔍</div>
      <input id="q" type="search" placeholder="search (tree filter / page filter)" />
    </div>
  </header>

  <main class="main">
    <section class="panel left">
      <div class="header">
        <div style="font-weight:900; font-size:18px;">{left_header_title}</div>
        <div style="color:var(--muted); font-weight:700; font-size:13px;">{left_header_sub}</div>
      </div>
      <div class="left-body" id="leftBody">
{left_body_html}
      </div>
    </section>

    <div class="splitter" id="splitter" title="drag to resize"></div>

    <section class="panel right">
      <div class="breadcrumb" id="breadcrumb">{right_breadcrumb}</div>
      <div class="viewer-area" id="viewerArea">
        <iframe id="viewer" title="viewer" scrolling="no" sandbox="allow-same-origin allow-popups allow-forms"></iframe>
      </div>
    </section>
  </main>

  <script>
    window.RULENAVI_CFG = {{
      buildBaseUrl: "{build_base_url}",
      pageId: "{page_id_for_js}"
    }};
  </script>
  {tree_script}
  <script src="./assets/app.js"></script>
</body>
</html>
"""


def write_text(path: Path, text: str, log: Logger) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    log.info(f"write: {path}")


def write_all_pages(
    *,
    out_dir: Path,
    site_title: str,
    build_base_url: str,
    has_icon: bool,
    icon_filename: str,
    nav_pages: List[Tuple[str, str, str]],
    log: Logger,
) -> None:
    # TOP(index.html)
    top_left = """
<div class="stub-card">
  <h2>TOP</h2>
  <p>ここはTOPページ（ダミー）です。今後、ダッシュボードやショートカットを置けます。</p>
</div>
""".strip()
    write_text(
        out_dir / "index.html",
        build_page_html(
            site_title=site_title,
            page_title="TOP",
            active_nav_id="top",
            build_base_url=build_base_url,
            has_icon=has_icon,
            icon_filename=icon_filename,
            left_header_title="メニュー",
            left_header_sub="今後拡張予定",
            left_body_html=top_left,
            right_breadcrumb="TOP",
            page_id_for_js="top",
            include_tree_data=False,
            nav_pages=nav_pages,
        ),
        log,
    )

    # 基準一覧(rules.html)
    rules_left = "<!-- rules tree will be rendered by app.js -->"
    write_text(
        out_dir / "rules.html",
        build_page_html(
            site_title=site_title,
            page_title="基準一覧",
            active_nav_id="rules",
            build_base_url=build_base_url,
            has_icon=has_icon,
            icon_filename=icon_filename,
            left_header_title="分類ツリー",
            left_header_sub="クリックで本文表示",
            left_body_html=rules_left,
            right_breadcrumb="ready",
            page_id_for_js="rules",
            include_tree_data=True,
            nav_pages=nav_pages,
        ),
        log,
    )

    # stubs
    def write_stub(page_id: str, title: str, filename: str) -> None:
        left_html = f"""
<div class="stub-card">
  <h2>{title}</h2>
  <p>このページは今後実装予定です。</p>
  <p>左ペインにはツリーやフィルタ等、右ペインには本文/MD表示を載せる想定です。</p>
</div>
""".strip()
        write_text(
            out_dir / filename,
            build_page_html(
                site_title=site_title,
                page_title=title,
                active_nav_id=page_id,
                build_base_url=build_base_url,
                has_icon=has_icon,
                icon_filename=icon_filename,
                left_header_title=title,
                left_header_sub="Coming soon",
                left_body_html=left_html,
                right_breadcrumb=title,
                page_id_for_js=page_id,
                include_tree_data=False,
                nav_pages=nav_pages,
            ),
            log,
        )

    write_stub("products", "製品", "products.html")
    write_stub("services", "サービス", "services.html")
    write_stub("search", "検索", "search.html")
    write_stub("wiki", "wiki", "wiki.html")
    write_stub("howto", "How to", "howto.html")
