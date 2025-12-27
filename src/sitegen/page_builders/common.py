# -*- coding: utf-8 -*-
##
# @file src/sitegen/page_builders/common.py
# @brief Common helpers for per-page HTML generation.
#
# @if japanese
# ページ生成で共有するナビHTML組み立てや設定埋め込みを提供します。
# 入力: サイトタイトルやベースURL、左/右ペインHTML、ツリー読み込み有無など。
# 出力: 完成したHTML文字列または書き込み結果のログのみで、ロジックやデータは変更しません。
# 注意: ここでは表示用テキストをそのまま埋め込むため、呼び出し側でエスケープ済みであることが前提です。
# @endif
#
# @if english
# Provides shared helpers for building navigation and page HTML fragments.
# Input: site title, base URL, left/right pane HTML, tree-data flag, and context metadata.
# Output: full HTML strings or write operations only; no business logic or data is modified here.
# Note: Callers must pre-escape any HTML snippets because they are injected verbatim.
# @endif
#
from __future__ import annotations

import json  # [JP] 標準: JSONシリアライズ / [EN] Standard: JSON serialization
from dataclasses import dataclass  # [JP] 標準: dataclass定義 / [EN] Standard: dataclass definition
from pathlib import Path  # [JP] 標準: パス操作 / [EN] Standard: path utilities
from typing import Dict, List, Optional, Tuple  # [JP] 標準: 型ヒント / [EN] Standard: type hints

from sitegen.logger import Logger  # [JP] 自作: ロガー / [EN] Local: logger utility
from textio import write_text_utf8  # [JP] 自作: UTF-8書き込みヘルパ / [EN] Local: UTF-8 write helper

# [JP] ナビゲーションタプル型 (id, label, href) / [EN] Navigation tuple type (id, label, href)
NavPages = List[Tuple[str, str, str]]


@dataclass(frozen=True)
##
# @brief Shared context for page writers / ページwriter共通のコンテキスト
#
# @if japanese
# ページ生成に必要な出力ディレクトリ、タイトル、ベースURL、アイコン情報、ナビページ、ロガーを保持します。
# @endif
#
# @if english
# Holds output directory, titles, base URL, icon info, navigation pages, and logger required by page writers.
# @endif
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


##
# @brief Build navigation HTML tabs / ナビゲーションのタブHTMLを生成する
#
# @if japanese
# nav_pagesの定義を基にタブリンクを生成し、active_idに一致するタブへis-activeクラスを付与します。
# @endif
#
# @if english
# Generates navigation tab links from nav_pages and adds the is-active class to the matching active_id.
# @endif
#
# @param active_id [in]  アクティブなタブID / Active tab id
# @param nav_pages [in]  (id,label,href)のリスト / List of (id, label, href)
# @return str  生成したHTML文字列 / Generated HTML string

def build_nav_html(active_id: str, nav_pages: NavPages) -> str:
    parts: List[str] = []
    # [JP] タブ単位でリンクを組み立てアクティブ状態を付与 / [EN] Build each tab link and mark active state
    for pid, label, href in nav_pages:
        cls = "tab is-active" if pid == active_id else "tab"
        parts.append(f'<a class="{cls}" href="./{href}" data-nav="{pid}">{label}</a>')
    return "\n".join(parts)


##
# @brief Build a full HTML page / 単一ページのHTML全文を組み立てる
#
# @if japanese
# サイトタイトルやベースURL、左右パネルのHTMLなどを受け取り、window.RULENAVI_CFGを含む完全なHTMLを返します。
# tree_data.jsや追加スクリプトの読み込み有無を切り替えられます。
# @endif
#
# @if english
# Assembles a full HTML document using site title, base URL, left/right body HTML, and embeds window.RULENAVI_CFG.
# Allows toggling tree_data.js and extra scripts/styles inclusion.
# @endif
#
# @param site_title [in]  サイトタイトル / Site title
# @param page_title [in]  ページタイトル / Page title
# @param active_nav_id [in]  アクティブタブID / Active nav id
# @param build_base_url [in]  ビルドベースURL / Build base URL
# @param has_icon [in]  アイコン有無 / Whether icon exists
# @param icon_filename [in]  アイコンファイル名 / Icon filename
# @param left_header_title [in]  左ヘッダ見出し / Left header title
# @param left_header_sub [in]  左ヘッダサブタイトル / Left header subtitle
# @param left_body_html [in]  左ペイン本文HTML / Left pane body HTML
# @param right_breadcrumb [in]  右パンくず / Right breadcrumb text
# @param page_id_for_js [in]  JS用ページID / Page id for JS config
# @param include_tree_data [in]  tree_data.js読込の有無 / Whether to include tree_data.js
# @param nav_pages [in]  ナビゲーションリスト / Navigation list
# @param cfg_extra [in]  RULENAVI_CFGへ追加する辞書 / Extra config for RULENAVI_CFG
# @param extra_head_html [in]  headへ挿入する追加HTML / Extra HTML to inject into head
# @param extra_body_scripts [in]  body終端へ追加するscriptパス / Extra scripts appended after app.js
# @return str  完成したHTML文字列 / Completed HTML string
# @details
# @if japanese
# - アイコン表示HTMLとナビHTMLを組み立てる。
# - cfg_extraがあればwindow.RULENAVI_CFGにマージする。
# - tree_data.jsと追加スクリプトの読み込みをフラグで切り替える。
# - テンプレートに全データを埋め込み文字列として返す。
# @endif
# @if english
# - Build icon and navigation HTML first.
# - Merge cfg_extra into window.RULENAVI_CFG when provided.
# - Toggle tree_data.js and extra scripts via flags.
# - Embed all pieces into the template and return the HTML string.
# @endif

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
    """
    # [JP] アイコン表示とナビHTMLを組み立て / [EN] Build icon markup and navigation HTML
    icon_html = (
        f'<img class="icon-img" src="./assets/{icon_filename}" alt="icon" />'
        if has_icon
        else '<div class="icon-emoji">??</div>'
    )
    nav_html = build_nav_html(active_nav_id, nav_pages)

    # [JP] RULENAVI_CFGを初期化し必要なら追加情報をマージ / [EN] Initialize RULENAVI_CFG and merge extras if any
    cfg = {
        "buildBaseUrl": str(build_base_url),
        "pageId": str(page_id_for_js),
    }
    if cfg_extra:
        cfg.update(cfg_extra)

    # [JP] tree_data.jsや追加スクリプトの読み込みタグを準備 / [EN] Prepare script tags for tree data and extra scripts
    tree_script = '<script src="./data/tree_data.js" charset="utf-8"></script>' if include_tree_data else ""
    extra_scripts_html = ""
    if extra_body_scripts:
        extra_scripts_html = "\n".join([f'<script src="{s}" charset="utf-8"></script>' for s in extra_body_scripts])

    # [JP] 埋め込み設定と本文をテンプレートへ反映 / [EN] Embed configuration and bodies into the template
    return f"""<!doctype html>
<html lang="ja">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{page_title} - {site_title}</title>
  <link rel="stylesheet" href="./assets/site.css" charset="utf-8" />
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
      <div>??</div>
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
  <script src="./assets/app.js" charset="utf-8"></script>
  {extra_scripts_html}
</body>
</html>
"""


##
# @brief Write text file with logging / テキストファイルを書き込みログ出力する
#
# @if japanese
# 親ディレクトリを用意してUTF-8で書き込み、パスをログに残します。
# @endif
#
# @if english
# Ensures the parent directory exists, writes UTF-8 text, and logs the destination path.
# @endif
#
# @param path [in]  出力パス / Output path
# @param text [in]  書き込む内容 / Text content
# @param log [in]  Loggerインスタンス / Logger instance

def write_text(path: Path, text: str, log: Logger) -> None:
    # [JP] ディレクトリ作成後にUTF-8で保存 / [EN] Create directories then save as UTF-8
    path.parent.mkdir(parents=True, exist_ok=True)
    write_text_utf8(path, text)
    log.info(f"write: {path}")


##
# @brief Build stub left-pane HTML / スタブ左ペインのHTMLを生成する
#
# @if japanese
# 未実装ページ向けのStubカードHTMLを返します。文言は元実装のまま保持します。
# @endif
#
# @if english
# Returns stub-card HTML for yet-to-be-implemented pages, preserving the original wording.
# @endif
#
# @param title [in]  見出しタイトル / Heading title
# @return str  左ペイン用HTML / Left-pane HTML

def stub_left_html(title: str) -> str:
    return f"""
<div class="stub-card">
  <h2>{title}</h2>
  <p>このページは今後実装予定です。</p>
  <p>左ペインにはツリーやフィルタ等、右ペインには本文/MD表示を載せる想定です。</p>
</div>
""".strip()