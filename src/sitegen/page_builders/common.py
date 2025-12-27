# -*- coding: utf-8 -*-
##
# @file src/sitegen/page_builders/common.py
# @brief Common helpers for per-page HTML generation.
#
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from sitegen.logger import Logger


NavPages = List[Tuple[str, str, str]]


@dataclass(frozen=True)
class SiteContext:
    """
    Shared context for page writers.
    """
    out_dir: Path
    site_title: str
    build_base_url: str
    has_icon: bool
    icon_filename: str
    nav_pages: NavPages
    log: Logger


def build_nav_html(active_id: str, nav_pages: NavPages) -> str:
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
    nav_pages: NavPages,
    cfg_extra: Optional[Dict[str, object]] = None,
    extra_head_html: str = "",
    extra_body_scripts: Optional[List[str]] = None,
) -> str:
    """
    Assemble a complete HTML page.
    - cfg_extra: window.RULENAVI_CFG に追加したいキー（将来ページ個別JS用）
    - extra_head_html: head に差し込む（ページ固有CSSなど）
    - extra_body_scripts: app.js の後に読みたいページ固有JSなど
    """
    icon_html = (
        f'<img class="icon-img" src="./assets/{icon_filename}" alt="icon" />'
        if has_icon
        else '<div class="icon-emoji">🦌</div>'
    )
    nav_html = build_nav_html(active_nav_id, nav_pages)

    cfg = {
        "buildBaseUrl": str(build_base_url),
        "pageId": str(page_id_for_js),
    }
    if cfg_extra:
        cfg.update(cfg_extra)

    tree_script = '<script src="./data/tree_data.js"></script>' if include_tree_data else ""
    extra_scripts_html = ""
    if extra_body_scripts:
        extra_scripts_html = "\n".join([f'<script src="{s}"></script>' for s in extra_body_scripts])

    return f"""<!doctype html>
<html lang="ja">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{page_title} - {site_title}</title>
  <link rel="stylesheet" href="./assets/site.css" />
  {extra_head_html}
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
    window.RULENAVI_CFG = {json.dumps(cfg, ensure_ascii=False)};
  </script>
  {tree_script}
  <script src="./assets/app.js"></script>
  {extra_scripts_html}
</body>
</html>
"""


def write_text(path: Path, text: str, log: Logger) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    log.info(f"write: {path}")


def stub_left_html(title: str) -> str:
    return f"""
<div class="stub-card">
  <h2>{title}</h2>
  <p>このページは今後実装予定です。</p>
  <p>左ペインにはツリーやフィルタ等、右ペインには本文/MD表示を載せる想定です。</p>
</div>
""".strip()
