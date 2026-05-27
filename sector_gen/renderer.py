import math
from pathlib import Path

from .coordinates import hex_distance, parse_canonical_id
from .config import SUBSECTOR_COLS, SUBSECTOR_ROWS, SUBSECTOR_LETTERS, SECTOR_SUBSECTORS_WIDE, SECTOR_SUBSECTORS_TALL
from .generator import ensure_raw_fields


# ---------------------------------------------------------------------------
# Hex geometry (flat-top hexagons)
# ---------------------------------------------------------------------------

def _hex_center(col: int, row: int, size: float, margin: float) -> tuple:
    """Pixel center (x, y) for a flat-top hex at grid position (col, row).
    col and row are 1-based. Odd columns shift down by size * sqrt(3) / 2."""
    horiz = 1.5 * size
    vert = math.sqrt(3) * size
    x = margin + (col - 1) * horiz + size
    y = margin + (row - 1) * vert + vert / 2
    if col % 2 == 1:  # odd columns shift down
        y += vert / 2
    return x, y


def _hex_vertices(cx: float, cy: float, size: float) -> list:
    """Six vertices of a flat-top hexagon centered at (cx, cy)."""
    vertices = []
    for i in range(6):
        angle = math.radians(60 * i)
        vertices.append((cx + size * math.cos(angle), cy + size * math.sin(angle)))
    return vertices


def _pts(vertices: list) -> str:
    return ' '.join(f"{x:.2f},{y:.2f}" for x, y in vertices)


# ---------------------------------------------------------------------------
# SVG building blocks
# ---------------------------------------------------------------------------

def _svg_hex(cx, cy, size, fill='none', stroke='#888', stroke_width=0.5) -> str:
    verts = _hex_vertices(cx, cy, size)
    return (f'<polygon points="{_pts(verts)}" fill="{fill}" '
            f'stroke="{stroke}" stroke-width="{stroke_width}"/>')


def _svg_circle(cx, cy, r, fill='#000') -> str:
    return f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{r}" fill="{fill}"/>'


def _svg_text(x, y, text, font_size=6, anchor='middle', fill='#000') -> str:
    return (f'<text x="{x:.2f}" y="{y:.2f}" font-size="{font_size}" '
            f'text-anchor="{anchor}" fill="{fill}" font-family="monospace">'
            f'{_esc(text)}</text>')


def _svg_line(x1, y1, x2, y2, stroke='#333', stroke_width=1, dash='') -> str:
    dash_attr = f' stroke-dasharray="{dash}"' if dash else ''
    return (f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" '
            f'stroke="{stroke}" stroke-width="{stroke_width}"{dash_attr}/>')


def _esc(s: str) -> str:
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def _display_profile(profile: str) -> str:
    """Format a profile string for SVG display only.
    Replaces Dx='-' (position 6) with '.' so the separator dash at position 7
    is never doubled, without touching the TSV format."""
    if len(profile) >= 7 and profile[6] == '-':
        return profile[:6] + '.' + profile[7:]
    return profile


# ---------------------------------------------------------------------------
# Route extraction
# ---------------------------------------------------------------------------

def _extract_routes(systems: dict, scope_ids: set) -> list:
    """Reconstruct route list from profile/notes for systems in scope."""
    routes = []
    seen = set()
    for sid, s in systems.items():
        if sid not in scope_ids:
            continue
        notes = s.get('notes', '')
        for tag in notes.split(';'):
            tag = tag.strip()
            if not tag.startswith('route:'):
                continue
            parts = tag.split(':')
            if len(parts) < 3:
                continue
            target, tier = parts[1], parts[2]
            key = tuple(sorted([sid, target]))
            if key not in seen:
                seen.add(key)
                routes.append((sid, target, tier))
    return routes


def _infer_routes_from_ni(systems: dict, scope_ids: set) -> list:
    """Derive intra-scope routes by scoring Ni pairs (fallback when notes lack route tags)."""
    from .network import calc_routes
    subscope = {}
    for sid in scope_ids:
        if sid in systems:
            s = systems[sid]
            if s.get('nr', 'I') != 'I':
                ensure_raw_fields(s)
                subscope[sid] = s
                ni = s.get('ni', '')
                s['_ni'] = int(ni) if ni else 0
    return calc_routes(subscope)


# ---------------------------------------------------------------------------
# Render a subsector
# ---------------------------------------------------------------------------

def render_subsector(systems: dict, region: str, sector_name: str, subsector: str,
                     size: float = 28.0, show_profile: bool = False,
                     color: bool = False) -> str:
    margin = size * 2
    width = margin * 2 + SUBSECTOR_COLS * 1.5 * size + size * 0.5
    height = margin * 2 + (SUBSECTOR_ROWS + 0.5) * math.sqrt(3) * size

    # Scale-dependent sizes
    coord_fs  = max(4, size * 0.22)   # hex coordinate label
    profile_fs = max(3, size * 0.19)  # SEP profile string
    name_fs   = max(4, size * 0.24)   # system name
    dot_r     = max(2, size * 0.11)   # system dot radius
    coord_y_offset  = -size * 0.50    # above center, upper-inner area
    profile_y_offset = size * 0.22    # just below center dot
    name_y_offset    = size * 0.48    # below profile

    scope_ids = set()
    for c in range(1, SUBSECTOR_COLS + 1):
        for r in range(1, SUBSECTOR_ROWS + 1):
            from .coordinates import build_canonical_id
            scope_ids.add(build_canonical_id(region, sector_name, subsector, c, r))

    lines = []
    lines.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width:.0f}" height="{height:.0f}">'
    )
    lines.append('<rect width="100%" height="100%" fill="white"/>')

    # Hex grid — outline + grey coordinate label in upper-inner area of every hex
    for col in range(1, SUBSECTOR_COLS + 1):
        for row in range(1, SUBSECTOR_ROWS + 1):
            cx, cy = _hex_center(col, row, size, margin)
            from .coordinates import build_canonical_id
            cid = build_canonical_id(region, sector_name, subsector, col, row)
            s = systems.get(cid)
            fill = 'none'
            if s and color:
                hz = s.get('_hz', 0)
                intensity = int(hz / 5 * 180)
                fill = f'rgb({255 - intensity // 2},{255 - intensity},{255 - intensity})'
            lines.append(_svg_hex(cx, cy, size * 0.95, fill=fill))
            coord_label = f"{col:02d}{row:02d}"
            lines.append(_svg_text(cx, cy + coord_y_offset, coord_label,
                                   font_size=coord_fs, fill='#aaa'))

    # Routes
    note_routes = _extract_routes(systems, scope_ids)
    inferred_routes = _infer_routes_from_ni(systems, scope_ids)
    all_routes = note_routes if note_routes else inferred_routes

    tier_style = {
        'Primary':   (4.0, '#000', ''),
        'Secondary': (1.75, '#222', ''),
        'Tertiary':  (0.75, '#999', '6,3'),
    }
    for sid1, sid2, tier in all_routes:
        s1 = systems.get(sid1)
        s2 = systems.get(sid2)
        if not s1 or not s2:
            continue
        p1 = parse_canonical_id(sid1)
        p2 = parse_canonical_id(sid2)
        cx1, cy1 = _hex_center(p1['col'], p1['row'], size, margin)
        cx2, cy2 = _hex_center(p2['col'], p2['row'], size, margin)
        sw, stroke, dash = tier_style.get(tier, (0.5, '#aaa', ''))
        if color and tier == 'Primary':
            stroke = '#00f'
        lines.append(_svg_line(cx1, cy1, cx2, cy2, stroke=stroke, stroke_width=sw, dash=dash))

    # System dots, SEP profile, and name
    for col in range(1, SUBSECTOR_COLS + 1):
        for row in range(1, SUBSECTOR_ROWS + 1):
            from .coordinates import build_canonical_id
            cid = build_canonical_id(region, sector_name, subsector, col, row)
            s = systems.get(cid)
            if not s:
                continue
            cx, cy = _hex_center(col, row, size, margin)
            lines.append(_svg_circle(cx, cy, dot_r))
            lines.append(_svg_text(cx, cy + profile_y_offset, _display_profile(s['profile']),
                                   font_size=profile_fs))
            lines.append(_svg_text(cx, cy + name_y_offset, s['name'],
                                   font_size=name_fs))

    # Subsector label
    lines.append(_svg_text(margin / 2, margin / 2, f"{sector_name}-{subsector}",
                           font_size=10, anchor='start'))

    lines.append('</svg>')
    return '\n'.join(lines)


# ---------------------------------------------------------------------------
# Render a sector (4×4 subsectors)
# ---------------------------------------------------------------------------

def render_sector(systems: dict, region: str, sector_name: str,
                  sub_size: float = 14.0, show_profile: bool = False,
                  color: bool = False) -> str:
    sub_margin = sub_size
    sub_w = sub_margin * 2 + SUBSECTOR_COLS * 1.5 * sub_size + sub_size * 0.5
    sub_h = sub_margin * 2 + (SUBSECTOR_ROWS + 0.5) * math.sqrt(3) * sub_size
    total_w = sub_w * SECTOR_SUBSECTORS_WIDE
    total_h = sub_h * SECTOR_SUBSECTORS_TALL

    lines = []
    lines.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{total_w:.0f}" height="{total_h:.0f}">'
    )
    lines.append('<rect width="100%" height="100%" fill="white"/>')

    for idx, sub_letter in enumerate(SUBSECTOR_LETTERS):
        sub_col_idx = idx % SECTOR_SUBSECTORS_WIDE
        sub_row_idx = idx // SECTOR_SUBSECTORS_WIDE
        ox = sub_col_idx * sub_w
        oy = sub_row_idx * sub_h

        svg = render_subsector(systems, region, sector_name, sub_letter,
                               size=sub_size, show_profile=show_profile, color=color)
        inner = svg.split('\n')[2:-1]  # strip outer svg tags
        lines.append(f'<g transform="translate({ox:.0f},{oy:.0f})">')
        lines.extend(inner)
        lines.append('</g>')

        # Subsector boundary
        lines.append(
            f'<rect x="{ox:.0f}" y="{oy:.0f}" width="{sub_w:.0f}" height="{sub_h:.0f}" '
            f'fill="none" stroke="#000" stroke-width="1"/>'
        )

    lines.append('</svg>')
    return '\n'.join(lines)


# ---------------------------------------------------------------------------
# Render a region (multiple sectors)
# ---------------------------------------------------------------------------

def render_region(systems: dict, sectors: list, cols: int = 2,
                  sub_size: float = 7.0, show_profile: bool = False,
                  color: bool = False) -> str:
    sub_margin = sub_size
    sub_w = sub_margin * 2 + SUBSECTOR_COLS * 1.5 * sub_size + sub_size * 0.5
    sub_h = sub_margin * 2 + (SUBSECTOR_ROWS + 0.5) * math.sqrt(3) * sub_size
    sector_w = sub_w * SECTOR_SUBSECTORS_WIDE
    sector_h = sub_h * SECTOR_SUBSECTORS_TALL
    rows = math.ceil(len(sectors) / cols)
    total_w = sector_w * cols
    total_h = sector_h * rows

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{total_w:.0f}" height="{total_h:.0f}">',
        '<rect width="100%" height="100%" fill="white"/>',
    ]

    for i, (region, sector_name) in enumerate(sectors):
        sc = i % cols
        sr = i // cols
        ox = sc * sector_w
        oy = sr * sector_h
        svg = render_sector(systems, region, sector_name, sub_size=sub_size,
                            show_profile=show_profile, color=color)
        inner = svg.split('\n')[2:-1]
        lines.append(f'<g transform="translate({ox:.0f},{oy:.0f})">')
        lines.extend(inner)
        lines.append('</g>')

    lines.append('</svg>')
    return '\n'.join(lines)


# ---------------------------------------------------------------------------
# Public render entry point
# ---------------------------------------------------------------------------

def render(systems: dict, scope: str, scope_id: str, output: Path,
           show_profile: bool = False, color: bool = False) -> None:
    """Render systems to an SVG file."""
    if scope == 'subsector':
        parts = _parse_scope_id_subsector(scope_id)
        svg = render_subsector(systems, parts['region'], parts['sector_name'],
                               parts['subsector'], show_profile=show_profile, color=color)
    elif scope == 'sector':
        parts = _parse_scope_id_sector(scope_id)
        svg = render_sector(systems, parts['region'], parts['sector_name'],
                            show_profile=show_profile, color=color)
    else:
        raise ValueError(f"Unsupported render scope: {scope!r}")

    output.write_text(svg, encoding='utf-8')


def _parse_scope_id_sector(scope_id: str) -> dict:
    """Parse REGION-SECTORNAME-NUMBER or REGION-SECTORNAME."""
    parts = scope_id.split('-')
    if len(parts) == 3:
        return {'region': parts[0], 'sector_name': parts[1], 'sector_number': parts[2]}
    elif len(parts) == 2:
        return {'region': parts[0], 'sector_name': parts[1], 'sector_number': '01'}
    raise ValueError(f"Invalid sector scope ID {scope_id!r}. Expected REGION-NAME-NUM")


def _parse_scope_id_subsector(scope_id: str) -> dict:
    """Parse REGION-SECTORNAME-NUMBER-LETTER or REGION-SECTORNAME-LETTER."""
    parts = scope_id.split('-')
    if len(parts) == 4:
        return {'region': parts[0], 'sector_name': parts[1],
                'sector_number': parts[2], 'subsector': parts[3]}
    elif len(parts) == 3:
        return {'region': parts[0], 'sector_name': parts[1],
                'sector_number': '01', 'subsector': parts[2]}
    raise ValueError(f"Invalid subsector scope ID {scope_id!r}. Expected REGION-NAME-NUM-LETTER")
