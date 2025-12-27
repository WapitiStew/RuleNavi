# -*- coding: utf-8 -*-
##
# @file src/sitegen/pages.py
# @brief HTML page builders for static site.
#
# @if japanese
# 静的サイト向けのナビゲーションタブと各ページHTMLを組み立て、指定パスへ書き出します。
# 入力: サイトタイトルやベースURL、ツリーJSONの有無、アイコン有無、左右パネルの本文HTML。
# 出力: 完成したHTML文字列をファイルへ保存します。ロジックやデータは変更しません。
# 注意: 渡されたHTML文字列をそのまま埋め込むため、エスケープ済みであることを前提とします。
# @endif
#
# @if english
# Builds navigation tabs and full page HTML for the static site, then writes them to disk.
# Input: site title, base URL, tree-data flag, icon presence, and left/right panel HTML strings.
# Output: finalized HTML documents saved to files without altering underlying logic or data.
# Note: Caller must supply pre-escaped HTML strings because they are injected as-is.
# @endif
#

from __future__ import annotations

from pathlib import Path  # [JP] 標準: パス操作 / [EN] Standard: path utilities
from typing import List, Tuple  # [JP] 標準: 型ヒント / [EN] Standard: type hints

from sitegen.logger import Logger  # [JP] 自作: ログ出力 / [EN] Local: logger utility
from textio import write_text_utf8  # [JP] 自作: UTF-8書き込みヘルパ / [EN] Local: UTF-8 write helper

# [JP] ナビゲーション用の(page_id, ラベル, ファイル名)定義 / [EN] Navigation definitions: (page_id, label, filename)
NAV_PAGES: List[Tuple[str, str, str]] = [
    ("top", "TOP", "index.html"),
    ("products", "製品", "products.html"),
    ("services", "サービス", "services.html"),
    ("rules", "基準一覧", "rules.html"),
    ("search", "検索", "search.html"),
    ("wiki", "wiki", "wiki.html"),
    ("howto", "How to", "howto.html"),
]


##
# @brief Build navigation HTML tabs / ナビゲーションのタブHTMLを生成する
#
# @if japanese
# nav_pagesに基づきタブリンクを生成し、active_idに一致するタブへis-activeクラスを付与します。
# @endif
#
# @if english
# Generates navigation tab links from nav_pages, adding is-active class to the tab matching active_id.
# @endif
#
# @param active_id [in]  アクティブなタブID / Active tab id
# @param nav_pages [in]  (id,label,href)のリスト / List of (id, label, href)
# @return str  生成したHTML文字列 / Generated HTML

def build_nav_html(active_id: str, nav_pages: List[Tuple[str, str, str]]) -> str:
    parts: List[str] = []
    # [JP] タブごとにリンクを生成しアクティブ状態を付与 / [EN] Build each tab link and mark active state
    for pid, label, href in nav_pages:
        cls = "tab is-active" if pid == active_id else "tab"
        parts.append(f'<a class="{cls}" href="./{href}" data-nav="{pid}">{label}</a>')
    return "\n".join(parts)


##
# @brief Build a full HTML page / 単一ページのHTML全文を組み立てる
#
# @if japanese
# サイトタイトル、ナビゲーション、左右パネルのHTML、アイコンやtree_data.jsの有無を受け取り、完全なHTML文字列を返します。
# iframe内で表示するためのデータ属性や設定オブジェクト(window.RULENAVI_CFG)も埋め込みます。
# @endif
#
# @if english
# Assembles a complete HTML page using site title, navigation, left/right panel content, icon/tree_data.js flags,
# and embeds configuration (window.RULENAVI_CFG) for iframe rendering.
# @endif
#
# @param site_title [in]  サイトタイトル / Site title
# @param page_title [in]  ページタイトル / Page title
# @param active_nav_id [in]  アクティブタブID / Active nav id
# @param build_base_url [in]  ビルドベースURL / Build base URL
# @param has_icon [in]  アイコン有無 / Whether icon exists
# @param icon_filename [in]  アイコンファイル名 / Icon filename
# @param left_header_title [in]  左パネル見出し / Left header title
# @param left_header_sub [in]  左パネルサブタイトル / Left header subtitle
# @param left_body_html [in]  左パネル本文HTML / Left body HTML
# @param right_breadcrumb [in]  右側パンくず / Right breadcrumb text
# @param page_id_for_js [in]  JS用ページID / Page id for JS config
# @param include_tree_data [in]  tree_data.jsを含めるか / Whether to include tree_data.js
# @param nav_pages [in]  ナビゲーションリスト / Navigation entries
# @return str  完成したHTML文字列 / Completed HTML string
# @details
# @if japanese
# - アイコンとナビHTMLを先に構築する。
# - tree_data.jsを読み込むかをフラグで切り替える。
# - window.RULENAVI_CFGへベースURLとページIDを埋め込みiframe表示に備える。
# - f-stringで完成HTMLを組み立てて返す。
# @endif
# @if english
# - Build icon and navigation HTML first.
# - Toggle tree_data.js inclusion based on the flag.
# - Inject base URL and page id into window.RULENAVI_CFG for iframe rendering.
# - Assemble the final HTML via f-string and return it.
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
    nav_pages: List[Tuple[str, str, str]],
) -> str:
    # [JP] アイコン表示用HTMLとナビゲーションを生成 / [EN] Build icon markup and navigation HTML
    icon_html = (
        f'<img class="icon-img" src="./assets/{icon_filename}" alt="icon" />'
        if has_icon
        else '<div class="icon-emoji">??</div>'
    )
    nav_html = build_nav_html(active_nav_id, nav_pages)

    # [JP] 左ペインでツリーを使う場合のみtree_data.jsを追加 / [EN] Include tree_data.js only when the left pane needs it
    tree_script = '<script src="./data/tree_data.js" charset="utf-8"></script>' if include_tree_data else ""

    # [JP] 組み立て済みパーツをテンプレートへ埋め込む / [EN] Inject prepared parts into the HTML template
    return f"""<!doctype html>
<html lang=\"ja\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>{page_title} - {site_title}</title>
  <link rel=\"stylesheet\" href=\"./assets/site.css\" charset=\"utf-8\" />
</head>
<body>
  <header class=\"topbar\">
    <div style=\"display:flex; align-items:center; gap:10px; min-width:0;\">
      <button class=\"brand\" id=\"brandHome\" title=\"Home\">
        {icon_html}
        <div class=\"title\">{site_title}</div>
      </button>
      <nav class=\"nav\" aria-label=\"site nav\">
{nav_html}
      </nav>
    </div>
    <div></div>
    <div class=\"search\">
      <div>??</div>
      <input id=\"q\" type=\"search\" placeholder=\"search (tree filter / page filter)\" />
    </div>
  </header>

  <main class=\"main\">
    <section class=\"panel left\">
      <div class=\"header\">
        <div style=\"font-weight:900; font-size:18px;\">{left_header_title}</div>
        <div style=\"color:var(--muted); font-weight:700; font-size:13px;\">{left_header_sub}</div>
      </div>
      <div class=\"left-body\" id=\"leftBody\">
{left_body_html}
      </div>
    </section>

    <div class=\"splitter\" id=\"splitter\" title=\"drag to resize\"></div>

    <section class=\"panel right\">
      <div class=\"breadcrumb\" id=\"breadcrumb\">{right_breadcrumb}</div>
      <div class=\"viewer-area\" id=\"viewerArea\">
        <iframe id=\"viewer\" title=\"viewer\" scrolling=\"no\" sandbox=\"allow-same-origin allow-popups allow-forms\"></iframe>
      </div>
    </section>
  </main>

  <script>
    window.RULENAVI_CFG = {{
      buildBaseUrl: \"{build_base_url}\",
      pageId: \"{page_id_for_js}\"
    }};
  </script>
  {tree_script}
  <script src=\"./assets/app.js\" charset=\"utf-8\"></script>
</body>
</html>
"""


##
# @brief Write text to file with logging / テキストをファイルへ書き込みログ出力する
# @if japanese
# 親ディレクトリを作成し、UTF-8でテキストを書き込んでからログへ出力します。
# @endif
#
# @if english
# Ensures parent directory exists, writes UTF-8 text, and logs the destination path.
# @endif
#
# @param path [in]  出力パス / Target path
# @param text [in]  書き込む内容 / Text content
# @param log [in]  Loggerインスタンス / Logger instance

def write_text(path: Path, text: str, log: Logger) -> None:
    # [JP] 親ディレクトリを用意してUTF-8で保存 / [EN] Ensure parent directory exists and save as UTF-8
    write_text_utf8(path, text)
    log.info(f"write: {path}")


##
# @brief Generate all static pages / 全ての静的ページを生成する
# @if japanese
# TOPとrulesページを生成し、残りのページはスタブとしてwrite_stubで出力します。アイコンやtree_dataの有無を反映し、書き込み後にログを出します。
# @endif
#
# @if english
# Generates TOP and rules pages plus stub pages for others via write_stub, reflecting icon and tree_data availability, and logs each write.
# @endif
#
# @param out_dir [in]  出力ディレクトリ / Output directory
# @param site_title [in]  サイトタイトル / Site title
# @param build_base_url [in]  ビルドベースURL / Build base URL
# @param has_icon [in]  アイコン有無 / Whether icon exists
# @param icon_filename [in]  アイコンファイル名 / Icon filename
# @param nav_pages [in]  ナビページリスト / Navigation pages list
# @param log [in]  Loggerインスタンス / Logger instance
# @details
# @if japanese
# - TOP(index.html)とrules.htmlを特別処理し、残りはwrite_stubで共通処理。
# - write_stubは左パネルにStubカードを入れ、ページIDとタイトルでHTMLを生成。
# - 生成ファイルはwrite_textで書き込み、ログを残す。
# @endif
# @if english
# - Handles TOP(index.html) and rules.html specially; others use write_stub helper.
# - write_stub inserts a stub card on the left and builds HTML using the page id/title.
# - Files are written via write_text with logging.
# @endif

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
    # [JP] TOPページ用の左ペインHTMLを定義 / [EN] Define left-pane HTML for TOP page
    top_left = """
<div class=\"stub-card\">
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
            left_header_title="分類ツリー",
            left_header_sub="クリックで本文表示",
            left_body_html=top_left,
            right_breadcrumb="TOP",
            page_id_for_js="top",
            include_tree_data=False,
            nav_pages=nav_pages,
        ),
        log,
    )

    # [JP] 基準一覧ページ用の左ペインを準備 / [EN] Prepare left pane for rules listing page
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

    # [JP] スタブページを共通処理で生成 / [EN] Generate stub pages via shared helper
    ##
    # @brief Write stub page HTML / スタブページのHTMLを書く
    #
    # @if japanese
    # タイトルから左ペインのStubカードを作成し、page_idに応じたナビ状態でHTMLを生成します。
    # @endif
    #
    # @if english
    # Builds stub card HTML from the title and renders the page with the specified page_id navigation state.
    # @endif
    #
    # @param page_id [in]  ページID / Page id
    # @param title [in]  ページタイトル / Page title
    # @param filename [in]  出力ファイル名 / Output filename

    def write_stub(page_id: str, title: str, filename: str) -> None:
        """
        Stub page writer for product/service/wiki/etc.
        """
        # [JP] 左ペイン用のStubカードHTMLを生成 / [EN] Build stub card HTML for the left pane
        left_html = f"""
<div class=\"stub-card\">
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