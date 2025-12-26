# -*- coding: utf-8 -*-
from __future__ import annotations

import shutil
from pathlib import Path

from sitegen.logger import Logger


def build_site_css() -> str:
    # 共通CSS（全ページ）
    return r"""
:root{
  --bg:#0f1115;
  --panel:#141823;
  --text:#e7e9ee;
  --muted:#a9afbf;
  --border:#242a3a;
  --shadow:0 10px 25px rgba(0,0,0,.25);

  --leftw: 360px;
  --splitw: 10px;
  --leftw-min: 240;
  --leftw-max: 720;
}
*{box-sizing:border-box}
html,body{height:100%}
body{
  margin:0;
  background: radial-gradient(1200px 500px at 20% 0%, rgba(122,162,247,.18), rgba(0,0,0,0)),
              radial-gradient(900px 400px at 80% 0%, rgba(42,195,222,.12), rgba(0,0,0,0)),
              var(--bg);
  color:var(--text);
  font-family:ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,"Noto Sans JP",Arial,"Hiragino Kaku Gothic ProN","Yu Gothic UI","Yu Gothic",Meiryo,sans-serif;
}

/* top bar */
.topbar{
  position:sticky; top:0; z-index:10;
  display:grid; grid-template-columns:auto 1fr auto;
  gap:12px; align-items:center;
  padding:12px 16px;
  background:rgba(15,17,21,.66);
  backdrop-filter:blur(12px);
  border-bottom:1px solid var(--border);
}
.brand{
  display:inline-flex; align-items:center; gap:10px;
  cursor:pointer; border:0; background:transparent;
  padding:6px 8px; border-radius:12px;
  color:var(--text);
}
.brand:hover{background:rgba(255,255,255,.04)}
.icon-img{
  width:36px;height:36px;border-radius:10px;
  border:1px solid rgba(255,255,255,.12);
  object-fit:cover;background:rgba(255,255,255,.06);
  box-shadow:var(--shadow);
}
.icon-emoji{
  width:36px;height:36px;border-radius:10px;
  display:grid;place-items:center;
  background:linear-gradient(145deg, rgba(122,162,247,.35), rgba(42,195,222,.18));
  border:1px solid rgba(255,255,255,.10);
  box-shadow:var(--shadow);
  font-size:18px;
}
.brand .title{font-weight:800;font-size:22px}

/* nav tabs (nowrap + horizontal scroll to keep header height stable) */
.nav{
  display:inline-flex;
  align-items:center;
  gap:8px;
  margin-left:12px;
  flex-wrap:nowrap;
  overflow-x:auto;
  overflow-y:hidden;
  white-space:nowrap;
  max-width:min(900px,55vw);
  padding-bottom:2px;
}
.nav::-webkit-scrollbar{height:0px;}
.nav{scrollbar-width:none; -ms-overflow-style:none;}

.tab{
  display:inline-flex;
  align-items:center;
  padding:8px 12px;
  border-radius:999px;
  border:1px solid rgba(255,255,255,.10);
  background:rgba(0,0,0,.18);
  color:var(--text);
  text-decoration:none;
  font-weight:800;
  font-size:13px;
  flex:0 0 auto;
}
.tab:hover{background:rgba(255,255,255,.04)}
.tab.is-active{
  background:rgba(122,162,247,.20);
  box-shadow:0 0 0 1px rgba(122,162,247,.25) inset;
}

.search{
  display:inline-flex; align-items:center;
  border:1px solid var(--border);
  border-radius:999px;
  padding:6px 10px;
  background:rgba(0,0,0,.20);
  gap:8px;
  min-width:260px;
}
.search input{
  border:0; outline:none; background:transparent;
  color:var(--text); width:100%; font-size:14px;
}

/* main layout */
.main{
  display:grid;
  grid-template-columns: var(--leftw) var(--splitw) 1fr;
  gap:0px;
  padding:14px 14px 18px;
  height:calc(100vh - 74px);
  min-height:0;
}
.panel{
  background:rgba(20,24,35,.72);
  border:1px solid var(--border);
  border-radius:16px;
  box-shadow:var(--shadow);
  overflow:hidden;
  min-height:0;
}

/* splitter */
.splitter{
  position:relative;
  display:block;
  cursor:col-resize;
  user-select:none;
  margin:0 6px;
}
.splitter::before{
  content:"";
  position:absolute;
  top:10px; bottom:10px;
  left:50%;
  width:2px;
  transform:translateX(-50%);
  background:rgba(255,255,255,.10);
  border-radius:2px;
}
.splitter:hover::before{ background:rgba(122,162,247,.35); }
.splitter.is-dragging::before{ background:rgba(122,162,247,.55); }

/* left */
.left{display:grid; grid-template-rows:auto 1fr; min-height:0;}
.left .header{
  padding:14px 14px 10px;
  border-bottom:1px solid rgba(255,255,255,.06);
  display:flex; justify-content:space-between; align-items:baseline;
  gap:10px;
}
.left-body{padding:12px 10px 14px; overflow:auto; min-height:0;}

/* right */
.right{display:flex; flex-direction:column; min-height:0;}
.breadcrumb{
  padding:12px 14px;
  border-bottom:1px solid rgba(255,255,255,.06);
  font-weight:800;
  color:var(--muted);
  text-align:center;
  flex:0 0 auto;
}
.viewer-area{
  flex:1 1 auto;
  min-height:0;
  overflow:auto;
  padding:12px 14px 18px;
}
#viewer{
  width:100%;
  border:0;
  background:transparent;
  display:block;
  height:600px;
}

/* tree */
.node{
  display:flex; align-items:center; gap:8px;
  padding:7px 10px; border-radius:12px;
  cursor:pointer; user-select:none;
}
.node:hover{background:rgba(255,255,255,.04)}
.node.is-selected{
  background:rgba(122,162,247,.18);
  box-shadow:0 0 0 1px rgba(122,162,247,.22) inset;
}
.twisty{width:18px; color:var(--muted); font-weight:900; text-align:center; flex:0 0 18px;}
.label{flex:1 1 auto; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; font-weight:700;}
.children{margin-left:20px; padding-left:8px; border-left:1px dashed rgba(255,255,255,.12);}

/* stub card */
.stub-card{
  width:100%;
  border:1px solid rgba(255,255,255,.10);
  border-radius:14px;
  background:linear-gradient(180deg, rgba(255,255,255,.03), rgba(255,255,255,0));
  box-shadow:var(--shadow);
  padding:18px 18px 22px;
}
.stub-card h2{margin:6px 0 10px;}
.stub-card p{margin:8px 0; color:var(--muted); line-height:1.7;}

@media (max-width: 900px){
  .main{grid-template-columns:1fr; height:auto;}
  .splitter{display:none;}
  .search{min-width:160px;}
  .nav{display:none;}
}
""".lstrip()


def build_app_js() -> str:
    # 共通JS：ページIDで分岐（rulesページだけツリー描画）
    return r"""/* assets/app.js */
(() => {
  const CFG = (window.RULENAVI_CFG || {});
  const pageId = String(CFG.pageId || "");
  const buildBaseUrl = String(CFG.buildBaseUrl || "");

  const viewerEl = document.getElementById("viewer");
  const viewerAreaEl = document.getElementById("viewerArea");
  const breadcrumbEl = document.getElementById("breadcrumb");
  const qEl = document.getElementById("q");
  const brandBtn = document.getElementById("brandHome");
  const splitterEl = document.getElementById("splitter");
  const leftBodyEl = document.getElementById("leftBody");

  function clamp(v, min, max) {
    v = Number(v);
    if (Number.isNaN(v)) return min;
    return Math.max(min, Math.min(max, v));
  }
  function getCssVarPx(name) {
    const s = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
    const m = String(s).match(/^(\d+(?:\.\d+)?)px$/);
    if (m) return Number(m[1]);
    const n = Number(s);
    return Number.isNaN(n) ? 0 : n;
  }
  function setLeftWidth(px) {
    document.documentElement.style.setProperty("--leftw", px + "px");
  }
  function initLeftWidthFromStorage() {
    try {
      const saved = localStorage.getItem("rulenavi_leftw_px");
      if (!saved) return;
      const min = getCssVarPx("--leftw-min") || 240;
      const max = getCssVarPx("--leftw-max") || 720;
      const v = clamp(parseInt(saved, 10), min, max);
      setLeftWidth(v);
    } catch (e) {}
  }
  function installSplitter(el) {
    if (!el) return;
    let dragging = false;

    function onDown(ev) {
      if (getComputedStyle(el).display === "none") return;
      dragging = true;
      el.classList.add("is-dragging");
      el.setPointerCapture && el.setPointerCapture(ev.pointerId);

      const min = getCssVarPx("--leftw-min") || 240;
      const max = getCssVarPx("--leftw-max") || 720;
      const mainEl = document.querySelector(".main");
      const mainLeft = mainEl ? mainEl.getBoundingClientRect().left : 0;

      function onMove(e) {
        if (!dragging) return;
        const newW = clamp(e.clientX - mainLeft - 14, min, max);
        setLeftWidth(newW);
      }
      function onUp() {
        if (!dragging) return;
        dragging = false;
        el.classList.remove("is-dragging");
        try {
          const cur = getCssVarPx("--leftw") || 360;
          localStorage.setItem("rulenavi_leftw_px", String(Math.round(cur)));
        } catch (ex) {}
        window.removeEventListener("pointermove", onMove);
        window.removeEventListener("pointerup", onUp);
      }

      window.addEventListener("pointermove", onMove);
      window.addEventListener("pointerup", onUp);
    }

    el.addEventListener("pointerdown", onDown);
  }

  function esc(s) {
    return String(s || "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;");
  }
  function joinUrl(base, path) {
    base = String(base || "");
    path = String(path || "");
    if (base !== "" && !base.endsWith("/")) base += "/";
    if (path.startsWith("/")) path = path.slice(1);
    return base + path;
  }
  function scrollViewerTop() {
    if (viewerAreaEl) viewerAreaEl.scrollTop = 0;
  }

  // iframe高さ追従（親側スクロール統一）
  window.addEventListener("message", (ev) => {
    const d = ev.data;
    if (!d || d.type !== "rulenavi_iframe_height") return;
    const h = Number(d.height);
    if (!Number.isFinite(h) || h <= 0) return;
    viewerEl.style.height = (h + 24) + "px";
  });

  function setBreadcrumb(text) {
    if (breadcrumbEl) breadcrumbEl.textContent = String(text || "");
  }

  function setViewerPlaceholder(title, message) {
    const t = String(title || "Ready");
    const m = String(message || "");
    const html = `<!doctype html>
<html lang="ja"><head><meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>${esc(t)}</title>
<style>
  :root{--bg:#0f1115;--text:#e7e9ee;--muted:#a9afbf;--border:#242a3a;--shadow:0 10px 25px rgba(0,0,0,.25);}
  html,body{height:auto;margin:0;}
  body{background:var(--bg);color:var(--text);font-family:ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,"Noto Sans JP",Arial,"Hiragino Kaku Gothic ProN","Yu Gothic UI","Yu Gothic",Meiryo,sans-serif;}
  .wrap{padding:22px;}
  .card{width:100%;border:1px solid var(--border);border-radius:14px;
        background:linear-gradient(180deg, rgba(255,255,255,.03), rgba(255,255,255,0));
        box-shadow:var(--shadow);padding:18px 18px 22px;}
  h2{margin:4px 0 10px;}
  p{margin:8px 0;color:var(--muted);line-height:1.7;}
</style></head><body>
  <div class="wrap"><div class="card"><h2>${esc(t)}</h2><p>${esc(m)}</p></div></div>
<script>
(() => {
  let last=-1;
  function calc(){const de=document.documentElement,b=document.body;return Math.max(de.scrollHeight,b.scrollHeight,de.offsetHeight,b.offsetHeight);}
  function post(){const h=calc();if(h===last)return;last=h;try{parent.postMessage({type:"rulenavi_iframe_height",height:h},"*");}catch(e){}}
  window.addEventListener("load",()=>{post();setTimeout(post,50);setTimeout(post,250);});
  window.addEventListener("resize",post);
  try{new MutationObserver(post).observe(document.body,{subtree:true,childList:true,attributes:true,characterData:true});}catch(e){}
  try{new ResizeObserver(post).observe(document.body);}catch(e){}
  post();
})();
</script>
</body></html>`;
    viewerEl.srcdoc = html;
    viewerEl.style.height = "600px";
    scrollViewerTop();
  }

  // 共通：ホームへ
  if (brandBtn) {
    brandBtn.addEventListener("click", () => {
      location.href = "./index.html";
    });
  }

  initLeftWidthFromStorage();
  installSplitter(splitterEl);

  // ------------------------------------------------------------
  // rules ページのみ：ツリー描画
  // ------------------------------------------------------------
  if (pageId !== "rules") {
    // stub
    setBreadcrumb(pageId || "ready");
    setViewerPlaceholder("Coming soon", "このページは今後実装予定です。");
    return;
  }

  const TREE = (window.RULENAVI_TREE || []);
  const LS_KEY_TREE_STATE = "rulenavi_tree_state_v1";

  const state = { selectedId:"", openSet:new Set(), filter:"" };

  function saveTreeState() {
    try {
      const obj = { open: Array.from(state.openSet), selectedId: state.selectedId || "" };
      localStorage.setItem(LS_KEY_TREE_STATE, JSON.stringify(obj));
    } catch (e) {}
  }
  function loadTreeState() {
    try {
      const s = localStorage.getItem(LS_KEY_TREE_STATE);
      if (!s) return;
      const obj = JSON.parse(s);
      state.openSet = new Set(obj.open || []);
      state.selectedId = obj.selectedId || "";
    } catch (e) {}
  }

  function nodeIdFromPath(n) {
    const p = String(n.path || "");
    return p !== "" ? p : ("_node_" + String(n.label || ""));
  }
  function hasChildren(n) {
    return Array.isArray(n.children) && n.children.length > 0;
  }
  function isBodyNode(n) {
    return !!n.has_body;
  }
  function bodyHtmlRel(n) {
    const p = String(n.path || "");
    if (p === "") return "";
    return p.replaceAll("\\","/").replaceAll(/\/+$/g,"") + "/body.html";
  }

  function findNodeAndBreadcrumbs(nodes, targetId, crumbs) {
    for (const n of nodes) {
      const nid = nodeIdFromPath(n);
      const nextCrumbs = crumbs.concat([String(n.label || "")]);
      if (nid === targetId) return { node:n, crumbs:nextCrumbs };
      if (hasChildren(n)) {
        const r = findNodeAndBreadcrumbs(n.children, targetId, nextCrumbs);
        if (r) return r;
      }
    }
    return null;
  }

  function visibleByFilter(n, filterLower) {
    if (!filterLower) return true;
    const label = String(n.label || "").toLowerCase();
    if (label.includes(filterLower)) return true;
    if (hasChildren(n)) for (const c of n.children) if (visibleByFilter(c, filterLower)) return true;
    return false;
  }
  function shouldAutoOpen(n, filterLower) {
    if (!filterLower) return false;
    if (!hasChildren(n)) return false;
    for (const c of n.children) if (visibleByFilter(c, filterLower)) return true;
    return false;
  }

  const treeContainer = document.createElement("div");
  treeContainer.id = "tree";
  leftBodyEl.innerHTML = "";
  leftBodyEl.appendChild(treeContainer);

  function render() {
    treeContainer.innerHTML = "";
    const filterLower = String(state.filter || "").trim().toLowerCase();
    const frag = document.createDocumentFragment();

    function renderNode(n, parentEl) {
      if (!visibleByFilter(n, filterLower)) return;

      const nid = nodeIdFromPath(n);
      const row = document.createElement("div");
      row.className = "node" + (state.selectedId === nid ? " is-selected" : "");

      const twist = document.createElement("div");
      twist.className = "twisty";
      const expandable = hasChildren(n);
      const opened = state.openSet.has(nid) || shouldAutoOpen(n, filterLower);
      twist.textContent = expandable ? (opened ? "▾" : "▸") : "•";

      const label = document.createElement("div");
      label.className = "label";
      label.textContent = String(n.label || "");

      function toggleOpenOnly() {
        if (!expandable) return;
        if (state.openSet.has(nid)) state.openSet.delete(nid);
        else state.openSet.add(nid);
        saveTreeState();
        render();
      }

      function openDocument() {
        state.selectedId = nid;
        saveTreeState();

        const res = findNodeAndBreadcrumbs(TREE, nid, []);
        const crumbs = (res && res.crumbs) ? res.crumbs : [String(n.label || "")];
        setBreadcrumb(crumbs.filter(x => x && x.trim() !== "").join(" / ") || "ready");

        const rel = bodyHtmlRel(n);
        if (rel) {
          const url = joinUrl(buildBaseUrl, rel);
          viewerEl.removeAttribute("srcdoc");
          viewerEl.src = url;
          viewerEl.style.height = "600px";
          scrollViewerTop();
        } else {
          setViewerPlaceholder("No document", "このノードには本文がありません。");
        }
        render();
      }

      // 三角クリック：展開/収納（本文がない葉は必要なら本文へ）
      twist.addEventListener("click", (ev) => {
        ev.stopPropagation();
        if (expandable) toggleOpenOnly();
        else if (isBodyNode(n)) openDocument();
      });

      // 行クリック：本文がないなら展開/収納、本文ありなら本文へ
      row.addEventListener("click", () => {
        if (!isBodyNode(n)) {
          if (expandable) toggleOpenOnly();
          else {
            setBreadcrumb(String(n.label || ""));
            setViewerPlaceholder("No document", "このノードには本文がありません。");
            state.selectedId = nid;
            saveTreeState();
            render();
          }
          return;
        }
        openDocument();
      });

      row.appendChild(twist);
      row.appendChild(label);
      parentEl.appendChild(row);

      if (expandable && opened) {
        const box = document.createElement("div");
        box.className = "children";
        parentEl.appendChild(box);
        for (const c of n.children) renderNode(c, box);
      }
    }

    for (const n of TREE) renderNode(n, frag);
    treeContainer.appendChild(frag);
  }

  // 検索（ツリーフィルタ）
  let filterTimer = null;
  if (qEl) {
    qEl.addEventListener("input", () => {
      if (filterTimer) clearTimeout(filterTimer);
      filterTimer = setTimeout(() => {
        state.filter = String(qEl.value || "");
        render();
      }, 80);
    });
  }

  window.addEventListener("beforeunload", () => saveTreeState());

  loadTreeState();
  setBreadcrumb("ready");
  setViewerPlaceholder("Ready", "左のツリーから本文のあるノードを選択してください。");
  render();
})();
""".lstrip()


def write_assets(assets_dir: Path, log: Logger) -> None:
    css = build_site_css()
    js = build_app_js()

    (assets_dir / "site.css").write_text(css, encoding="utf-8")
    log.info(f"write: {assets_dir / 'site.css'}")

    (assets_dir / "app.js").write_text(js, encoding="utf-8")
    log.info(f"write: {assets_dir / 'app.js'}")


def copy_icon_if_exists(res_dir: Path, icon_name: str, assets_dir: Path, log: Logger) -> bool:
    src = (res_dir / icon_name).resolve()
    if src.exists() and src.is_file():
        dst = assets_dir / icon_name
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)
        log.info(f"copy icon: {src} -> {dst}")
        return True

    log.warn(f"icon not found: {src}  (use default emoji icon)")
    return False
