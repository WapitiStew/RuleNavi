# -*- coding: utf-8 -*-
from __future__ import annotations

import re
from typing import List


def md_to_html(md_text: str) -> str:
    lines = md_text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    out: List[str] = []
    in_code = False
    list_open = False

    def esc(s: str) -> str:
        return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    def close_list() -> None:
        nonlocal list_open
        if list_open:
            out.append("</ul>")
            list_open = False

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


def wrap_body_html(inner_html: str, title: str) -> str:
    # body.html は “どこから開かれても” スタイルが崩れないよう、基本は埋め込みCSS
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
