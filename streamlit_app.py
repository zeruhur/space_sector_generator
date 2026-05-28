"""streamlit_app.py — Streamlit web interface for the Space Sector Generator.

Deploy to streamlit.io; run locally with:
    streamlit run streamlit_app.py

Persistence model
-----------------
The workspace is stored in browser localStorage under the key "ssg_workspace"
(via streamlit-local-storage).  It survives page refreshes and tab reopens for
the same user in the same browser, without any server-side storage.

TSV import / export remains available as the portable backup / interchange
format — use it to transfer data between browsers or share with others.
"""

import json
import re
import tempfile
from pathlib import Path

import streamlit as st
from streamlit_local_storage import LocalStorage

from sector_gen.config import SUBSECTOR_LETTERS
from sector_gen.coordinates import derive_code, hexes_for_subsector
from sector_gen.generator import generate_system
from sector_gen.gui import _gen_sector, _gen_region
from sector_gen.io import load_tsv, merge, export_markdown, export_json, save_tsv
from sector_gen.names import load_register
from sector_gen.network import run_network_pass, resolve_pending_links
from sector_gen.renderer import render_subsector_to_svg, render_sector, render_region
from sector_gen.viewer import translate_system


# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Space Sector Generator",
    page_icon="🌌",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# localStorage — single instance for the whole app
# ---------------------------------------------------------------------------
_LS_KEY = "ssg_workspace"
_local = LocalStorage()

# ---------------------------------------------------------------------------
# Session state defaults
# ---------------------------------------------------------------------------
if "systems" not in st.session_state:
    st.session_state.systems = {}
if "_ws_loaded" not in st.session_state:
    st.session_state._ws_loaded = False

# ---------------------------------------------------------------------------
# Restore workspace from localStorage (once per browser session)
#
# streamlit-local-storage is async: getItem returns None on the very first
# Streamlit render (before the browser component responds), then triggers a
# rerun with the real value.  We gate on _ws_loaded so we restore exactly
# once and never overwrite data the user generated in the same session.
# ---------------------------------------------------------------------------
if not st.session_state._ws_loaded:
    _raw = _local.getItem(_LS_KEY)
    if _raw is not None:                   # component has responded
        try:
            _data = json.loads(_raw)
            if isinstance(_data, dict) and _data:
                st.session_state.systems = _data
        except (json.JSONDecodeError, TypeError):
            pass
        st.session_state._ws_loaded = True  # don't try again this session


# ---------------------------------------------------------------------------
# Persistence helpers
# ---------------------------------------------------------------------------

def _save_ws() -> None:
    """Write current workspace to localStorage."""
    _local.setItem(_LS_KEY, json.dumps(st.session_state.systems), key="ws_autosave")


def _clear_ws() -> None:
    """Wipe workspace from both session state and localStorage, then rerun."""
    st.session_state.systems = {}
    st.session_state._ws_loaded = True      # prevent stale restore on rerun
    _local.setItem(_LS_KEY, "{}", key="ws_clear")
    st.rerun()


# ---------------------------------------------------------------------------
# Generation helpers
# ---------------------------------------------------------------------------

def get_codes(region_name: str, sector_name: str) -> tuple:
    rc = derive_code(region_name, set())
    sc = derive_code(sector_name, set())
    return rc, sc, f"{sc}-01"


def do_generate(rc, sc, sid, scope, sub, n_sec, density, overwrite) -> None:
    register = load_register("default")
    systems = dict(st.session_state.systems)

    if scope == "Subsector":
        if overwrite:
            hexes = set(hexes_for_subsector(rc, sc, sub))
            systems = {k: v for k, v in systems.items() if k not in hexes}
        new = {}
        for cid in hexes_for_subsector(rc, sc, sub):
            s = generate_system(cid, sid, density=density, register=register)
            if s:
                new[cid] = s
        systems = merge(systems, new)
        sub_s = {k: v for k, v in systems.items()
                 if v.get("region") == rc and v.get("sector") == sid
                 and v.get("subsector") == sub}
        run_network_pass(sub_s)
        resolve_pending_links(systems)

    elif scope == "Sector":
        if overwrite:
            systems = {k: v for k, v in systems.items()
                       if not (v.get("region") == rc and v.get("sector") == sid)}
        systems = merge(systems, _gen_sector(rc, sc, sid, density, register))
        resolve_pending_links(systems)

    else:  # Region
        n = max(1, int(n_sec))
        if overwrite:
            systems = {k: v for k, v in systems.items() if v.get("region") != rc}
        new, _ = _gen_region(rc, n, density, register)
        systems = merge(systems, new)
        resolve_pending_links(systems)

    st.session_state.systems = systems
    _save_ws()


# ---------------------------------------------------------------------------
# Rendering helpers
# ---------------------------------------------------------------------------

def get_svg(systems: dict, scope: str, rc: str, sc: str, sid: str, sub: str):
    if not systems:
        return None
    if scope == "Subsector":
        return render_subsector_to_svg(systems, f"{rc}-{sid}-{sub}")
    elif scope == "Sector":
        return render_sector(systems, rc, sc)
    else:
        pairs = sorted({
            (s.get("region"), s.get("sector", "").split("-")[0])
            for s in systems.values()
            if s.get("region") == rc and s.get("sector")
        }, key=lambda x: x[1])
        return render_region(systems, pairs) if pairs else None


def scope_filter(systems: dict, scope: str, rc: str, sid: str, sub: str) -> dict:
    if scope == "Subsector":
        return {k: v for k, v in systems.items()
                if v.get("region") == rc and v.get("sector") == sid
                and v.get("subsector") == sub}
    elif scope == "Sector":
        return {k: v for k, v in systems.items()
                if v.get("region") == rc and v.get("sector") == sid}
    return {k: v for k, v in systems.items() if v.get("region") == rc}


def svg_responsive(svg: str) -> str:
    m = re.search(r'width="([\d.]+)"[^>]*height="([\d.]+)"', svg)
    if not m:
        return svg
    w, h = m.group(1), m.group(2)
    return re.sub(
        r'width="[\d.]+"([^>]*)height="[\d.]+"',
        f'viewBox="0 0 {w} {h}" width="100%" height="auto"\\1',
        svg, count=1,
    )


def build_pdf_html(systems: dict, *_args) -> str:
    """Delegate to the shared hierarchical PDF builder in io.py."""
    from sector_gen.io import build_print_html
    return build_print_html(systems)


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.title("🌌 Space Sector Generator")
    st.caption("Procedural interstellar sector generator for tabletop RPGs")
    st.divider()

    region_name = st.text_input("Region Name", "Orion")
    scope = st.selectbox("Scope", ["Subsector", "Sector", "Region"])

    sector_name = "Cassian"
    if scope != "Region":
        sector_name = st.text_input("Sector Name", "Cassian")
    else:
        st.caption("Sector names are auto-generated for region scope.")

    subsector_letter = "A"
    n_sectors = 4
    if scope == "Subsector":
        subsector_letter = st.selectbox("Subsector", list(SUBSECTOR_LETTERS))
    elif scope == "Region":
        n_sectors = int(st.number_input(
            "Number of Sectors", min_value=1, max_value=16, value=4, step=1
        ))

    density = st.selectbox("Density", ["sparse", "standard", "dense", "cluster"], index=1)
    overwrite = st.checkbox("Overwrite if exists")

    st.divider()
    col_g, col_v = st.columns(2)
    generate_clicked = col_g.button("⚡ Generate", use_container_width=True, type="primary")
    view_clicked = col_v.button("🔭 View", use_container_width=True)

    # Workspace status
    n_sys = len(st.session_state.systems)
    if n_sys:
        st.caption(f"Workspace: {n_sys} system{'s' if n_sys != 1 else ''} (auto-saved locally)")
    else:
        st.caption("Workspace: empty")

    st.divider()

    # TSV backup — import
    st.caption("TSV backup")
    uploaded = st.file_uploader("Import TSV", type=["tsv"], label_visibility="collapsed")
    if uploaded is not None:
        with tempfile.NamedTemporaryFile(suffix=".tsv", delete=False) as tf:
            tf.write(uploaded.read())
            tp = Path(tf.name)
        imported = load_tsv(tp)
        tp.unlink()
        st.session_state.systems = merge(st.session_state.systems, imported)
        _save_ws()
        st.success(f"Imported {len(imported)} systems")

    # TSV backup — export (full workspace)
    if st.session_state.systems:
        with tempfile.NamedTemporaryFile(suffix=".tsv", delete=False) as tf:
            tp = Path(tf.name)
        save_tsv(tp, st.session_state.systems)
        st.download_button(
            "Export workspace TSV",
            tp.read_bytes(),
            "workspace.tsv",
            "text/tab-separated-values",
            use_container_width=True,
        )
        tp.unlink(missing_ok=True)

        if st.button("🗑 Clear workspace", use_container_width=True):
            _clear_ws()


# ---------------------------------------------------------------------------
# Main area
# ---------------------------------------------------------------------------
tab_gen, tab_guide, tab_rules = st.tabs(["Generator", "User Guide", "System Rules"])

with tab_gen:
    rc, sc, sid = get_codes(region_name, sector_name)

    if generate_clicked:
        with st.spinner(f"Generating {scope.lower()}…"):
            try:
                do_generate(rc, sc, sid, scope, subsector_letter, n_sectors, density, overwrite)
                st.success(
                    f"✓ {scope} generated — workspace now has "
                    f"{len(st.session_state.systems)} systems (auto-saved to localStorage)"
                )
            except Exception as e:
                st.error(f"Generation failed: {e}")

    systems = st.session_state.systems
    svg = get_svg(systems, scope, rc, sc, sid, subsector_letter)

    if svg:
        st.subheader(f"{scope} Map — {rc} / {sc}")

        iframe_h = 680

        map_html = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8">
<style>
*{{margin:0;padding:0;box-sizing:border-box;}}
body{{background:#000;overflow:hidden;}}
#wrap{{position:relative;width:100%;height:{iframe_h - 4}px;overflow:hidden;
       background:#000;border-radius:6px;cursor:grab;user-select:none;}}
#wrap.dragging{{cursor:grabbing;}}
#scene{{position:absolute;top:0;left:0;transform-origin:0 0;}}
#controls{{position:absolute;top:8px;right:8px;z-index:20;
           display:flex;flex-direction:column;gap:4px;}}
.cb{{width:32px;height:32px;background:rgba(30,41,59,.9);color:#f1f5f9;
     border:1px solid #475569;border-radius:4px;font-size:1.1rem;
     cursor:pointer;display:flex;align-items:center;justify-content:center;}}
.cb:hover{{background:#475569;}}
#hint{{position:absolute;bottom:10px;left:50%;transform:translateX(-50%);
       background:rgba(15,23,42,.85);color:#38bdf8;border:1px solid #38bdf8;
       padding:3px 12px;border-radius:20px;font-size:.72rem;font-family:sans-serif;
       pointer-events:none;opacity:0;transition:opacity .3s;white-space:nowrap;}}
#wrap:hover #hint{{opacity:1;}}
</style></head><body>
<div id="wrap">
  <div id="controls">
    <div class="cb" id="zi">+</div>
    <div class="cb" id="zo">−</div>
    <div class="cb" id="zr">⟲</div>
  </div>
  <div id="hint">Scroll to zoom · Drag to pan</div>
  <div id="scene">{svg}</div>
</div>
<script>
(function(){{
  var wrap  = document.getElementById('wrap');
  var scene = document.getElementById('scene');
  var sc = 1, tx = 0, ty = 0, drag = false, ox, oy;

  function apply(){{
    scene.style.transform = 'translate('+tx+'px,'+ty+'px) scale('+sc+')';
  }}

  function fit(){{
    var el = scene.querySelector('svg');
    if (!el) return;
    var W = parseFloat(el.getAttribute('width'))  || el.viewBox.baseVal.width  || 800;
    var H = parseFloat(el.getAttribute('height')) || el.viewBox.baseVal.height || 600;
    var cW = wrap.offsetWidth || 800;
    var cH = wrap.offsetHeight || {iframe_h - 4};
    sc = Math.min(cW / W, cH / H);
    tx = (cW - W * sc) / 2;
    ty = (cH - H * sc) / 2;
    apply();
  }}

  function zoom(factor, cx, cy){{
    tx = cx - (cx - tx) * factor;
    ty = cy - (cy - ty) * factor;
    sc *= factor;
    apply();
  }}

  document.getElementById('zi').onclick = function(e){{
    e.stopPropagation();
    zoom(1.25, wrap.offsetWidth / 2, wrap.offsetHeight / 2);
  }};
  document.getElementById('zo').onclick = function(e){{
    e.stopPropagation();
    zoom(0.8, wrap.offsetWidth / 2, wrap.offsetHeight / 2);
  }};
  document.getElementById('zr').onclick = function(e){{
    e.stopPropagation(); fit();
  }};

  wrap.addEventListener('wheel', function(e){{
    e.preventDefault();
    var r = wrap.getBoundingClientRect();
    zoom(e.deltaY < 0 ? 1.1 : 0.9, e.clientX - r.left, e.clientY - r.top);
  }}, {{passive: false}});

  wrap.addEventListener('mousedown', function(e){{
    if (e.target.classList.contains('cb') || e.button !== 0) return;
    drag = true; wrap.classList.add('dragging');
    ox = e.clientX - tx; oy = e.clientY - ty;
  }});
  window.addEventListener('mousemove', function(e){{
    if (!drag) return;
    tx = e.clientX - ox; ty = e.clientY - oy; apply();
  }});
  window.addEventListener('mouseup', function(){{
    drag = false; wrap.classList.remove('dragging');
  }});

  wrap.addEventListener('touchstart', function(e){{
    if (e.touches.length === 1){{
      drag = true; ox = e.touches[0].clientX - tx; oy = e.touches[0].clientY - ty;
    }}
  }}, {{passive: true}});
  window.addEventListener('touchmove', function(e){{
    if (!drag || e.touches.length !== 1) return;
    tx = e.touches[0].clientX - ox; ty = e.touches[0].clientY - oy; apply();
  }}, {{passive: true}});
  window.addEventListener('touchend', function(){{ drag = false; }});

  window.addEventListener('load', fit);
  setTimeout(fit, 50);
}})();
</script>
</body></html>"""

        st.components.v1.html(map_html, height=iframe_h, scrolling=False)

        # System details picker
        visible = scope_filter(systems, scope, rc, sid, subsector_letter)
        if visible:
            st.divider()
            options = {f"{v['name']}  [{k}]": k for k, v in sorted(visible.items())}
            pick = st.selectbox(
                "Select a system to view its detail sheet",
                ["— none —"] + list(options.keys()),
            )
            if pick and pick != "— none —":
                sdata = systems[options[pick]]
                with st.expander(
                    f"**{sdata['name']}** — `{sdata.get('profile', '')}`", expanded=True
                ):
                    st.markdown(translate_system(sdata))

        # Scope-filtered export
        st.divider()
        st.subheader("Export")
        export_sys = scope_filter(systems, scope, rc, sid, subsector_letter)

        if export_sys:
            fname = (
                f"{rc}-{sc}-{subsector_letter}" if scope == "Subsector"
                else f"{rc}-{sc}" if scope == "Sector"
                else rc
            )
            c1, c2, c3, c4, c5 = st.columns(5)

            with tempfile.NamedTemporaryFile(suffix=".tsv", delete=False) as tf:
                tp = Path(tf.name)
            save_tsv(tp, export_sys)
            c1.download_button("TSV", tp.read_bytes(), f"{fname}.tsv",
                               "text/tab-separated-values", use_container_width=True)
            tp.unlink(missing_ok=True)

            with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tf:
                tp = Path(tf.name)
            export_json(tp, export_sys)
            c2.download_button("JSON", tp.read_bytes(), f"{fname}.json",
                               "application/json", use_container_width=True)
            tp.unlink(missing_ok=True)

            with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as tf:
                tp = Path(tf.name)
            export_markdown(tp, export_sys)
            c3.download_button("MD", tp.read_bytes(), f"{fname}.md",
                               "text/markdown", use_container_width=True)
            tp.unlink(missing_ok=True)

            c4.download_button("SVG", svg.encode("utf-8"), f"{fname}.svg",
                               "image/svg+xml", use_container_width=True)

            pdf_bytes = build_pdf_html(
                export_sys, scope, rc, sc, sid, subsector_letter
            ).encode("utf-8")
            c5.download_button(
                "PDF",
                pdf_bytes,
                f"{fname}-print.html",
                "text/html",
                help="Downloads a print-ready HTML file. Open in browser → Print → Save as PDF.",
                use_container_width=True,
            )
        else:
            st.info("No systems in the current scope to export.")

    else:
        st.info("Use the sidebar to generate a subsector, sector, or region.")

with tab_guide:
    guide = Path("STREAMLIT_GUIDE.md")
    if guide.exists():
        st.markdown(guide.read_text(encoding="utf-8"))
    else:
        st.warning("STREAMLIT_GUIDE.md not found.")

with tab_rules:
    rules = Path("sector_generation_system.md")
    if rules.exists():
        st.markdown(rules.read_text(encoding="utf-8"))
    else:
        st.warning("sector_generation_system.md not found.")
