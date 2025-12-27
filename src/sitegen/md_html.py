# -*- coding: utf-8 -*-
##
# @file src/sitegen/md_html.py
# @brief Lightweight Markdown to HTML converter for sitegen.
#
# @if japanese
# MarkdownテキストをシンプルなHTMLへ変換し、body.html用のラッパーも提供します。
# コードブロックやリスト、ヘッダを最低限サポートし、スクリプト側でIFrame高さ通知用のJSを付与します。
# 外部ライブラリを使わず、文字列操作のみで完結します。
# @endif
#
# @if english
# Converts Markdown text to minimal HTML and provides a wrapper for body.html output.
# Supports basic code blocks, lists, and headings, adding a JS helper for iframe height reporting.
# Uses only string processing without external libraries.
# @endif
#

from __future__ import annotations

import re  # [JP] 標準: 正規表現による行判定 / [EN] Standard: regex for line parsing
from typing import List  # [JP] 標準: 型ヒント用List / [EN] Standard: List type hint


##
# @brief Convert Markdown text to simple HTML / Markdownテキストを簡易HTMLへ変換する
#
# @if japanese
# Markdownのヘッダ(#/##/###)、箇条書き(-,*)、コードブロック```、空行を扱い、その他は<p>でラップします。
# エスケープは & < > のみを対象にし、コードブロック内はそのまま出力します。
# @endif
#
# @if english
# Handles headings (#/##/###), bullet lists (-,*), fenced code blocks ```, and blank lines, wrapping remaining lines in <p>.
# Escapes &, <, > outside code blocks while emitting raw content inside code fences.
# @endif
#
# @param md_text [in]  入力Markdownテキスト / Input Markdown text
# @return str  生成したHTML文字列 / Generated HTML string
# @details
# @if japanese
# - 改行コードをLFに正規化し行単位で処理する。
# - リスト開始/終了をclose_listで制御しネストは未対応。
# - コードブロック開始終了をin_codeで管理し、未終了の場合は閉じタグを追加する。
# @endif
# @if english
# - Normalizes newlines to LF and processes line by line.
# - Manages list opening/closing via close_list (no nesting support).
# - Tracks code block state with in_code and appends closing tags if left open.
# @endif
#
def md_to_html(md_text: str) -> str:
    lines = md_text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    out: List[str] = []
    in_code = False
    list_open = False

    # [JP] HTMLエスケープ補助 / [EN] Helper to escape HTML entities
    def esc(s: str) -> str:
        return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    # [JP] 箇条書きのクローズ制御 / [EN] Close list if open
    def close_list() -> None:
        nonlocal list_open
        if list_open:
            out.append("</ul>")
            list_open = False

    # [JP] 各行を判定してHTML化 / [EN] Convert each line based on pattern
    for line in lines:
        if re.match(r"^```(\w+)?\s*$", line):
            if not in_code:
                close_list()
                in_code = True
                out.append("<pre><code>")
            else:
                in_code = False
                out.append("</code></pre>")
            continue

        if in_code:
            out.append(esc(line))
            continue

        if line.startswith("### "):
            close_list()
            out.append(f"<h3>{esc(line[4:])}</h3>")
            continue
        if line.startswith("## "):
            close_list()
            out.append(f"<h2>{esc(line[3:])}</h2>")
            continue
        if line.startswith("# "):
            close_list()
            out.append(f"<h1>{esc(line[2:])}</h1>")
            continue

        m_li = re.match(r"^\s*[-*]\s+(.*)$", line)
        if m_li:
            if not list_open:
                out.append("<ul>")
                list_open = True
            out.append(f"<li>{esc(m_li.group(1))}</li>")
            continue

        if line.strip() == "":
            close_list()
            out.append("<div class='sp'></div>")
            continue

        close_list()
        out.append(f"<p>{esc(line)}</p>")

    close_list()
    if in_code:
        out.append("</code></pre>")
    return "\n".join(out)


##
# @brief JavaScript snippet to report iframe height / iframe高さ通知用のJSスニペット
#
# @if japanese
# body.html内から親フレームへ高さをpostMessageする即時関数の文字列を返します。
# @endif
#
# @if english
# Returns a script string that posts the document height to the parent frame via postMessage.
# @endif
#
# @return str  scriptタグ付きの文字列 / Script string with <script> tag
def _iframe_height_reporter_script() -> str:
    return r"""
<script>
(() => {
  let last = -1;
  function calc() {
    const de = document.documentElement;
    const b = document.body;
    return Math.max(de.scrollHeight, b.scrollHeight, de.offsetHeight, b.offsetHeight);
  }
  function post() {
    const h = calc();
    if (h === last) return;
    last = h;
    try { parent.postMessage({ type: "rulenavi_iframe_height", height: h }, "*"); } catch (e) {}
  }
  function tick() { post(); setTimeout(post, 50); setTimeout(post, 250); }
  window.addEventListener("load", tick);
  window.addEventListener("resize", post);
  try { new ResizeObserver(() => post()).observe(document.body); } catch (e) {}
  try {
    new MutationObserver(() => post()).observe(document.body, {
      subtree: true, childList: true, attributes: true, characterData: true
    });
  } catch (e) {}
  tick();
})();
</script>
"""


##
# @brief Wrap inner HTML into body.html template / inner HTMLをbody.html用テンプレートに包む
#
# @if japanese
# MD変換後のHTMLをカードデザイン付きのbody.htmlとして整形し、iframe高さ通知スクリプトを差し込みます。
# ページタイトルは引数titleをそのまま利用します。
# @endif
#
# @if english
# Formats converted Markdown HTML into a body.html layout with styling and embeds the iframe height reporter.
# Uses the provided title for the document title tag.
# @endif
#
# @param inner_html [in]  本文HTML / Inner HTML content
# @param title [in]  タイトル文字列 / Title string
# @return str  完成したbody.html文字列 / Final body.html string
def wrap_body_html(inner_html: str, title: str) -> str:
    # body.html は iframe 埋め込みを想定し、余計なスクリプトを避けて最小限のCSSを付与
    return f"""<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>{title}</title>
<style>
  :root {{
    --bg:#0f1115;
    --text:#e7e9ee;
    --muted:#a9afbf;
    --border:#242a3a;
    --shadow:0 10px 25px rgba(0,0,0,.25);
  }}
  *{{box-sizing:border-box}}
  html,body{{height:auto}}
  body{{
    margin:0;
    background:var(--bg);
    color:var(--text);
    font-family:ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,"Noto Sans JP",Arial,"Hiragino Kaku Gothic ProN","Yu Gothic UI","Yu Gothic",Meiryo,sans-serif;
  }}
  .doc{{padding:22px 22px 64px;}}
  .card{{
    width:100%;
    background:linear-gradient(180deg, rgba(255,255,255,.03), rgba(255,255,255,0));
    border:1px solid var(--border);
    border-radius:14px;
    box-shadow:var(--shadow);
    padding:18px 18px 22px;
  }}
  h1{{font-size:28px;margin:8px 0 16px}}
  h2{{font-size:20px;margin:22px 0 10px}}
  h3{{font-size:16px;margin:18px 0 8px;color:var(--muted)}}
  p{{margin:10px 0;line-height:1.7}}
  ul{{margin:10px 0 10px 22px;line-height:1.7}}
  pre{{
    overflow:auto;
    background:#0b0d12;
    border:1px solid var(--border);
    border-radius:12px;
    padding:12px;
  }}
  code{{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,"Noto Sans Mono",monospace}}
  .sp{{height:8px}}
</style>
</head>
<body>
  <div class="doc">
    <div class="card">
      {inner_html}
    </div>
  </div>
  {_iframe_height_reporter_script()}
</body>
</html>
"""
