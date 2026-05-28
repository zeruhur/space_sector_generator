# 🚀 User Guide: Space Sector Generator (Web Edition)

Welcome to the **Space Sector Generator** web app — a professional-grade worldbuilding tool for Game Masters and Sci-Fi writers, running entirely in your browser at [streamlit.io](https://streamlit.io).

No installation required. No account needed.

---

## 🛠️ Quick Start

1. **Set your names** — Enter a Region Name and Sector Name in the sidebar (e.g. *Orion* / *Cassian*). Short codes are derived automatically.
2. **Choose a scope** — Subsector (1 of 16), Sector (all 16 subsectors), or Region (multiple sectors at once).
3. **Click Generate** — The map appears in the main area.
4. **Click a system name** in the picker below the map to read its detail sheet.
5. **Export** what you need using the download buttons below the map.

---

## 🌐 The Interface

The app has three tabs:
- **Generator** — the main workspace (map, system details, export buttons)
- **User Guide** — this document
- **System Rules** — the full generation ruleset (profile codes, network algorithm, route tiers)

### Sidebar Controls

| Control | Purpose |
|:---|:---|
| **Region Name** | Human-readable name for the region (e.g. *Orion Terminus*). A short code is derived automatically. |
| **Sector Name** | Human-readable name for the sector (e.g. *Cassian*). |
| **Scope** | What to generate: a single subsector, the full 16-subsector sector, or a whole region. |
| **Subsector** | Letter A–P. Only visible when Scope = Subsector. |
| **Number of Sectors** | How many sectors to include in the region. Only visible when Scope = Region. |
| **Density** | Controls how populated hexes are: Sparse → Standard → Dense → Cluster. |
| **Overwrite if exists** | When checked, replaces any previously generated systems in the target scope. When unchecked, existing systems are preserved (additive generation). |
| **⚡ Generate** | Run the generator for the current scope and settings. |
| **🔭 View** | Refresh the display using the current sidebar settings and workspace data. |

### Import / Load Workspace

At the bottom of the sidebar you can **upload an existing TSV file** (previously exported from this app or from the desktop CLI). The loaded systems merge additively into the current session — existing systems are never overwritten on import.

Use **Clear workspace** to start fresh.

---

## 🗺️ The Map

The map renders as a scalable hex grid. Scroll inside it to see larger scopes. The map is read-only in this interface — click on it to pan, use the scroll wheel to zoom within the map viewport.

### Viewing System Details

Use the **Select a system** picker below the map to choose any system and read its full detail sheet in natural language:
- Intrinsic characteristics (access, hazard, resources, population, authority, tension, distinctiveness)
- Network position (importance and role in the interstellar trade network)
- GM notes

---

## 💾 Session vs. Persistence

**Important:** This is a stateless web app. Your workspace lives only in your current browser session — it is not saved anywhere. If you refresh the page or close the tab, your data is gone.

**Workflow to preserve your work:**

1. Generate your content.
2. **Export TSV** immediately after generating.
3. Next session: use the **Import TSV** uploader to reload your data.

The TSV file is the canonical save format — it is compact, human-readable, and can be re-imported at any time.

---

## 🌍 Generation Scopes

### Subsector
Generates one 8×10 hex subsector (up to 80 systems). The subsector letter A–P identifies its position in a 4×4 grid within the sector.

### Sector
Generates all 16 subsectors at once, producing a full 32×40 hex sector. Cross-subsector routes are automatically resolved. This can take a few seconds.

### Region
Generates multiple sectors (2–16), each named automatically. Each sector is a full 16-subsector grid. Use this to build a large-scale campaign setting in one click.

---

## 🔗 Cross-Subsector Routes

When a system is near a subsector boundary, the generator creates **pending links** to adjacent subsectors. These are automatically resolved into active trade routes when the neighbouring subsector is generated (subsector scope with additive generation, or any sector/region generation).

Route tiers:
- **Primary** — thick solid line, highest-traffic corridor
- **Secondary** — thin solid line
- **Tertiary** — dashed line, minor or frontier connection

---

## 📦 Export Formats

| Button | Format | Use case |
|:---|:---|:---|
| **TSV** | Tab-separated values | Save / reload your workspace; import into spreadsheets |
| **JSON** | JSON | Integration with other tools; programmatic access |
| **MD** | Markdown | Human-readable report with system index and detail sheets |
| **SVG** | Scalable vector graphic | High-quality printing of the sector map |
| **PDF** | Print-ready HTML | Downloads an HTML file; open it in your browser and **Print → Save as PDF** to get a full sector document with maps and system sheets |

The export scope always matches the sidebar scope: Subsector exports only that subsector's systems; Sector exports all systems in that sector; Region exports all systems for that region.

> **PNG export** is not available in the web edition. Use the **SVG** export and convert it with any vector editor or online tool, or use the desktop/CLI version of the app.

---

## 🪐 Advanced Topics

### Profile Format

Every system is described by a 7-character profile (e.g. `32M2A3X`) or a 10-character network profile (e.g. `32M2A3X-4K`):

| Position | Field | Values |
|:---|:---|:---|
| 1 | Access (Ac) | 0 Open → 5 Inaccessible |
| 2 | Hazard (Hz) | 0 Benign → 5 Lethal |
| 3 | Resources (Rx) | N T I M B S C X |
| 4 | Population (Pp) | 0 Empty → 5 Dense |
| 5 | Authority (Pw) | V A L C S H E |
| 6 | Tension (Tn) | 0 Stable → 5 Catastrophic |
| 7 | Distinctiveness (Dx) | - X P H T C R W |
| 9 | Network Importance (Ni) | 0–5 |
| 10 | Network Role (Nr) | B T H K F S I |

### Determinism

The generator is fully deterministic. A canonical ID like `ORI-CAS-A0101` always produces the same system profile and name across sessions, as long as you use the same version of the app. Your universe is stable — reloading a TSV will always show the same systems.

### Additive Generation

When **Overwrite if exists** is unchecked (the default), generating a new subsector leaves all pre-existing systems untouched. This lets you build a sector incrementally, one subsector at a time, with cross-boundary routes resolved automatically as you expand.

---

## 📝 GM Tips

- **Network Importance (Ni) 4–5**: The political and economic hubs of your sector. Focus faction conflicts and major NPCs here.
- **Tension (Tn) 4–5**: Active war zones or systemic collapse. Perfect starting locations for adventure.
- **Distinctiveness (Dx)**: Use this as your "oracle" — the one thing that makes a system worth visiting.
- **Access (Ac) 3–5**: Natural adventure hooks. Why is this system hard to reach, and what does that protect?
- **Chokepoint (Nr = K)**: Systems with network role K are strategic bottlenecks. Control one and you control a corridor.

---

## 🔁 Recommended Session Workflow

1. Generate Sector "Cassian" in Region "Orion" → **Export TSV** (save it).
2. Next session: Import the TSV → the full sector reloads instantly.
3. Switch scope to Subsector, select a specific letter, toggle "Overwrite if exists" → **Generate** to regenerate just that subsector.
4. **Export PDF** for a print-ready campaign document with all maps and detail sheets.

---

*Created by [zeruhur](https://github.com/zeruhur). Licensed under the MIT License.*
*Source: [github.com/zeruhur/space_sector_generator](https://github.com/zeruhur/space_sector_generator)*
