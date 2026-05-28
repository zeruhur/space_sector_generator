import csv
import json
import sys
from pathlib import Path

from .generator import parse_profile, ensure_raw_fields

TSV_FIELDS = ['id', 'profile', 'name', 'region', 'sector', 'subsector', 'col', 'row',
              'ni', 'nr', 'notes']


def load_tsv(path: Path) -> dict:
    """Load a TSV file and return a dict keyed by canonical ID."""
    systems = {}
    with path.open(newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            sid = row['id']
            system = {k: row.get(k, '') for k in TSV_FIELDS}
            # Parse raw fields from profile for later use
            try:
                fields = parse_profile(system['profile'])
                system.update({
                    '_ac': fields['ac'],
                    '_hz': fields['hz'],
                    '_rx': fields['rx'],
                    '_pp': fields['pp'],
                    '_pw': fields['pw'],
                    '_tn': fields['tn'],
                    '_dx': fields['dx'],
                    '_col': int(system['col']),
                    '_row': int(system['row']),
                })
                if fields['ni'] != '':
                    system['_ni'] = fields['ni']
                if fields['nr'] != '':
                    system['_nr'] = fields['nr']
            except (ValueError, KeyError):
                pass
            systems[sid] = system
    return systems


def save_tsv(path: Path, systems: dict) -> None:
    """Write all systems to a TSV file sorted by canonical ID."""
    with path.open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=TSV_FIELDS, delimiter='\t',
                                extrasaction='ignore')
        writer.writeheader()
        for sid in sorted(systems.keys()):
            writer.writerow({k: systems[sid].get(k, '') for k in TSV_FIELDS})


def write_tsv_stdout(systems: dict) -> None:
    writer = csv.DictWriter(sys.stdout, fieldnames=TSV_FIELDS, delimiter='\t',
                            extrasaction='ignore')
    writer.writeheader()
    for sid in sorted(systems.keys()):
        writer.writerow({k: systems[sid].get(k, '') for k in TSV_FIELDS})


def merge(existing: dict, new_systems: dict) -> dict:
    """Merge new systems into existing; existing entries win."""
    result = dict(existing)
    for sid, s in new_systems.items():
        if sid not in result:
            result[sid] = s
    return result


def _parse_notes_tags(notes: str) -> tuple:
    """Split a notes field into (routes, free_notes).
    routes: list of (target_id, tier); free_notes: list of plain strings."""
    routes, free = [], []
    for tag in notes.split(';'):
        tag = tag.strip()
        if not tag:
            continue
        if tag.startswith('route:'):
            parts = tag.split(':')
            if len(parts) >= 3:
                routes.append((parts[1], parts[2]))
        elif not tag.startswith('pending-link:'):
            free.append(tag)
    return routes, free


def export_markdown(path: Path, systems: dict) -> None:
    """Export systems to a hierarchically structured Markdown file."""
    from collections import defaultdict
    from .viewer import translate_profile_dict

    def _fields(s):
        t = translate_profile_dict(s['profile'])
        if 'error' in t:
            return None
        return dict(
            ac=t['access'].split(' - ')[0].split(' (')[0],
            hz=t['hazard'].split(' (')[0],
            rx=t['resources'].split(': ')[0].split(' / ')[0],
            pp=t['population'].split(' - ')[0],
            pw=t['power'].split(' - ')[0],
            tn=t['tension'].split(' - ')[0].split(', ')[0],
            dx=t['distinctiveness'].split(' - ')[0],
            net=(f"{t['net_importance'].split(' - ')[0]} ({t['net_role'].split(' - ')[0]})"
                 if t['net_importance'] else '—'),
            t=t,
        )

    def _hdr(extra=()):
        cols = ['System'] + list(extra) + [
            'Coordinates', 'Profile', 'Access', 'Hazard', 'Resources',
            'Population', 'Power', 'Tension', 'Distinct', 'Network',
        ]
        return ('| ' + ' | '.join(cols) + ' |\n'
                + '| ' + ' | '.join(['---'] * len(cols)) + ' |')

    def _row(sid, s, extra=()):
        f = _fields(s)
        if f is None:
            return None
        cells = [f'**{s["name"]}**'] + list(extra) + [
            f'`{sid}`', f'`{s["profile"]}`',
            f['ac'], f['hz'], f['rx'], f['pp'], f['pw'], f['tn'], f['dx'], f['net'],
        ]
        return '| ' + ' | '.join(cells) + ' |'

    def _sheet(sid, s):
        f = _fields(s)
        lines = [f'#### {s["name"]} — `{sid}` — `{s["profile"]}`', '']
        if f is None:
            lines += ['*Profile parse error*', '']
            return '\n'.join(lines)
        t = f['t']
        lines += [
            '**Intrinsic Characteristics**', '',
            f'- **Access (Ac):** {t["access"]}',
            f'- **Hazard (Hz):** {t["hazard"]}',
            f'- **Resources (Rx):** {t["resources"]}',
            f'- **Population (Pp):** {t["population"]}',
            f'- **Authority (Pw):** {t["power"]}',
            f'- **Tension (Tn):** {t["tension"]}',
            f'- **Distinctiveness (Dx):** {t["distinctiveness"]}',
            '',
        ]
        if t['net_importance']:
            lines += [
                '**Interstellar Network Position**', '',
                f'- **Importance (Ni):** {t["net_importance"]}',
                f'- **Network Role (Nr):** {t["net_role"]}',
                '',
            ]
        routes, free_notes = _parse_notes_tags(s.get('notes', ''))
        if routes:
            lines += ['**Routes**', ''] + [f'- `{tgt}` ({tier})' for tgt, tier in routes] + ['']
        if free_notes:
            lines += ['**GM Notes**', ''] + [f'*{n}*' for n in free_notes] + ['']
        lines += ['*(Space for GM annotations and local events)*', '']
        return '\n'.join(lines)

    grouped = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    for sid in sorted(systems.keys()):
        s = systems[sid]
        grouped[s.get('region', '?')][s.get('sector', '?')][s.get('subsector', '?')].append(sid)

    with path.open('w', encoding='utf-8') as out:
        for region in sorted(grouped.keys()):
            secs = grouped[region]
            out.write(f'# Region {region}\n\n')

            # Sector Index — one row per sector
            out.write('## Sector Index\n\n')
            out.write('| Sector | ID | Subsectors | Systems |\n')
            out.write('| --- | --- | --- | --- |\n')
            for sec in sorted(secs.keys()):
                sc_code = sec.split('-')[0]
                n_sub = len(secs[sec])
                n_sys = sum(len(secs[sec][sub]) for sub in secs[sec])
                out.write(f'| {sc_code} | {sec} | {n_sub} | {n_sys} |\n')
            out.write('\n---\n\n')

            for sec in sorted(secs.keys()):
                sc_code = sec.split('-')[0]
                out.write(f'## {sc_code} ({sec})\n\n')

                # Subsector Index — one row per subsector
                out.write('### Subsector Index\n\n')
                out.write('| Subsector | Code | Systems |\n')
                out.write('| --- | --- | --- |\n')
                for sub in sorted(secs[sec].keys()):
                    sub_code = f'{region}-{sc_code}-{sub}'
                    n_sys = len(secs[sec][sub])
                    out.write(f'| {sub} | {sub_code} | {n_sys} |\n')
                out.write('\n')

                for sub in sorted(secs[sec].keys()):
                    sub_code = f'{region}-{sc_code}-{sub}'
                    out.write(f'### Subsector {sub} — {sub_code}\n\n')

                    out.write('#### System Index\n\n')
                    out.write(_hdr() + '\n')
                    for sid in secs[sec][sub]:
                        row = _row(sid, systems[sid])
                        if row:
                            out.write(row + '\n')
                    out.write('\n')

                    for sid in secs[sec][sub]:
                        out.write(_sheet(sid, systems[sid]))
                        out.write('---\n\n')


def build_print_html(systems: dict) -> str:
    """Build a hierarchical print-ready HTML document.
    Groups systems automatically by region > sector > subsector."""
    import re as _re
    from collections import defaultdict
    from .viewer import translate_profile_dict
    from .renderer import render_subsector as _render_sub

    def _svg_fit(svg):
        m = _re.search(r'width="([\d.]+)"[^>]*height="([\d.]+)"', svg)
        if not m:
            return svg
        w, h = m.group(1), m.group(2)
        return _re.sub(
            r'width="[\d.]+"([^>]*)height="[\d.]+"',
            f'viewBox="0 0 {w} {h}" width="100%" height="auto"\\1',
            svg, count=1,
        )

    def _fields(s):
        t = translate_profile_dict(s['profile'])
        if 'error' in t:
            return None
        return dict(
            ac=t['access'].split(' - ')[0].split(' (')[0],
            hz=t['hazard'].split(' (')[0],
            rx=t['resources'].split(': ')[0].split(' / ')[0],
            pp=t['population'].split(' - ')[0],
            pw=t['power'].split(' - ')[0],
            tn=t['tension'].split(' - ')[0].split(', ')[0],
            dx=t['distinctiveness'].split(' - ')[0],
            net=(f"{t['net_importance'].split(' - ')[0]} ({t['net_role'].split(' - ')[0]})"
                 if t['net_importance'] else '—'),
            t=t,
        )

    def _row(sid, s, f=None, extra_tds=''):
        if f is None:
            f = _fields(s)
        if f is None:
            return ''
        return (f'<tr><td><b>{s["name"]}</b></td>{extra_tds}'
                f'<td><code>{sid}</code></td><td><code>{s["profile"]}</code></td>'
                f'<td>{f["ac"]}</td><td>{f["hz"]}</td><td>{f["rx"]}</td>'
                f'<td>{f["pp"]}</td><td>{f["pw"]}</td><td>{f["tn"]}</td>'
                f'<td>{f["dx"]}</td><td>{f["net"]}</td></tr>')

    def _table(rows_html, extra_th=''):
        head = (f'<th>System</th>{extra_th}'
                '<th>Coordinates</th><th>Profile</th>'
                '<th>Access</th><th>Hazard</th><th>Resources</th>'
                '<th>Population</th><th>Power</th><th>Tension</th>'
                '<th>Distinct</th><th>Network</th>')
        return (f'<table class="idx"><thead><tr>{head}</tr></thead>'
                f'<tbody>{rows_html}</tbody></table>')

    def _sheet(sid, s):
        f = _fields(s)
        h = (f'<h4>{s["name"]} &mdash; <code>{sid}</code>'
             f' &mdash; <code>{s["profile"]}</code></h4>')
        if f is None:
            return h + '<p><i>Profile parse error</i></p>'
        t = f['t']
        html = h + '<ul>'
        html += f'<li><b>Access (Ac):</b> {t["access"]}</li>'
        html += f'<li><b>Hazard (Hz):</b> {t["hazard"]}</li>'
        html += f'<li><b>Resources (Rx):</b> {t["resources"]}</li>'
        html += f'<li><b>Population (Pp):</b> {t["population"]}</li>'
        html += f'<li><b>Authority (Pw):</b> {t["power"]}</li>'
        html += f'<li><b>Tension (Tn):</b> {t["tension"]}</li>'
        html += f'<li><b>Distinctiveness (Dx):</b> {t["distinctiveness"]}</li>'
        html += '</ul>'
        if t['net_importance']:
            html += ('<p><b>Network Position:</b></p><ul>'
                     f'<li><b>Importance (Ni):</b> {t["net_importance"]}</li>'
                     f'<li><b>Network Role (Nr):</b> {t["net_role"]}</li></ul>')
        routes, free_notes = _parse_notes_tags(s.get('notes', ''))
        if routes:
            html += '<p><b>Routes:</b></p><ul>'
            for tgt, tier in routes:
                html += f'<li><code>{tgt}</code> ({tier})</li>'
            html += '</ul>'
        if free_notes:
            html += f'<p><b>GM Notes:</b> <i>{"; ".join(free_notes)}</i></p>'
        html += '<p><small><i>(Space for GM annotations and local events)</i></small></p>'
        return html

    grouped = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    for sid in sorted(systems.keys()):
        s = systems[sid]
        grouped[s.get('region', '?')][s.get('sector', '?')][s.get('subsector', '?')].append(sid)

    def _simple_table(header_row, data_rows):
        head = ''.join(f'<th>{h}</th>' for h in header_row)
        body = ''.join(
            '<tr>' + ''.join(f'<td>{c}</td>' for c in row) + '</tr>'
            for row in data_rows
        )
        return (f'<table class="idx"><thead><tr>{head}</tr></thead>'
                f'<tbody>{body}</tbody></table>')

    parts = []
    for region in sorted(grouped.keys()):
        secs = grouped[region]
        parts.append(f'<h1>Region {region}</h1>')

        # Sector Index — one row per sector
        sector_rows = []
        for sec in sorted(secs.keys()):
            sc_code = sec.split('-')[0]
            n_sub = len(secs[sec])
            n_sys = sum(len(secs[sec][sub]) for sub in secs[sec])
            sector_rows.append((sc_code, sec, str(n_sub), str(n_sys)))
        parts.append('<h2>Sector Index</h2>')
        parts.append(_simple_table(['Sector', 'ID', 'Subsectors', 'Systems'], sector_rows))

        for sec in sorted(secs.keys()):
            sc_code = sec.split('-')[0]
            parts.append(f'<div class="pgbrk"></div><h2>{sc_code} ({sec})</h2>')

            # Subsector Index — one row per subsector
            sub_rows = []
            for sub in sorted(secs[sec].keys()):
                sub_code = f'{region}-{sc_code}-{sub}'
                n_sys = len(secs[sec][sub])
                sub_rows.append((sub, sub_code, str(n_sys)))
            parts.append('<h3>Subsector Index</h3>')
            parts.append(_simple_table(['Subsector', 'Code', 'Systems'], sub_rows))

            for sub in sorted(secs[sec].keys()):
                sub_code = f'{region}-{sc_code}-{sub}'
                parts.append(
                    f'<div class="pgbrk"></div>'
                    f'<h3>Subsector {sub} &mdash; {sub_code}</h3>'
                )
                try:
                    parts.append(f'<div class="mapwrap">{_svg_fit(_render_sub(systems, region, sc_code, sub))}</div>')
                except Exception:
                    pass
                yrows = ''.join(_row(sid, systems[sid]) for sid in secs[sec][sub])
                parts.append('<div class="pgbrk"></div><h4>System Index</h4>')
                parts.append(_table(yrows))
                for sid in secs[sec][sub]:
                    parts.append(_sheet(sid, systems[sid]))
                    parts.append('<hr class="sep">')

    css = (
        'body{font-family:Georgia,serif;margin:2cm;color:#000;font-size:10pt;}'
        'h1{font-size:18pt;border-bottom:3px solid #000;padding-bottom:5pt;margin:0 0 14pt;}'
        'h2{font-size:15pt;border-bottom:2px solid #000;padding-bottom:4pt;margin:18pt 0 10pt;}'
        'h3{font-size:13pt;border-bottom:1px solid #555;padding-bottom:2pt;margin:14pt 0 8pt;}'
        'h4{font-size:11pt;border-bottom:1px dotted #aaa;margin:10pt 0 4pt;}'
        'code{font-family:monospace;background:#f0f0f0;padding:1pt 3pt;font-size:9pt;}'
        '.mapwrap{text-align:center;margin:8pt 0;}'
        '.mapwrap svg{max-height:480pt;width:90%;display:block;margin:auto;}'
        'table.idx{border-collapse:collapse;width:100%;font-size:7.5pt;margin:6pt 0;}'
        'table.idx th{background:#222;color:#fff;padding:3pt 5pt;text-align:left;font-size:7pt;}'
        'table.idx td{border:1px solid #ccc;padding:2pt 4pt;}'
        'table.idx tr:nth-child(even) td{background:#f8f8f8;}'
        'hr.sep{border:none;border-top:1px solid #ddd;margin:8pt 0;}'
        'ul{margin:2pt 0 6pt 18pt;} li{margin-bottom:2pt;}'
        '.pgbrk{page-break-before:always;}'
        '@media print{.pgbrk{page-break-before:always;}'
        'h1,h2,h3,h4{break-after:avoid;}.mapwrap{break-inside:avoid;}}'
    )
    return (
        '<!DOCTYPE html>\n<html lang="en"><head><meta charset="UTF-8">'
        '<title>Sector Export</title>'
        f'<style>{css}</style></head><body>'
        + ''.join(parts)
        + '<script>window.onload=function(){window.print();}</script>'
        + '</body></html>'
    )


def export_json(path: Path, systems: dict) -> None:
    """Export all systems to a JSON file."""
    data = {
        "metadata": {
            "system": "Sector Generation System",
            "count": len(systems)
        },
        "systems": [systems[sid] for sid in sorted(systems.keys())]
    }
    with path.open('w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)


def get_pending_links(systems: dict) -> list:
    """Return list of (source_id, target_id) for all pending-link entries."""
    pending = []
    for sid, s in systems.items():
        notes = s.get('notes', '')
        for tag in notes.split(';'):
            tag = tag.strip()
            if tag.startswith('pending-link:'):
                target = tag[len('pending-link:'):]
                pending.append((sid, target))
    return pending


def confirm_overwrite(path: Path) -> bool:
    """Prompt user for confirmation before overwriting. Returns True to proceed."""
    resp = input(f"Overwrite {path}? [y/N] ").strip().lower()
    return resp in ('y', 'yes')


def test():
    import tempfile

    # Build a minimal systems dict
    sample = {
        'ORT-CAS-A0101': {
            'id': 'ORT-CAS-A0101',
            'profile': '32M2A3X-4K',
            'name': 'Kethavar',
            'region': 'ORT',
            'sector': 'CAS-01',
            'subsector': 'A',
            'col': '01',
            'row': '01',
            'ni': '4',
            'nr': 'K',
            'notes': '',
        },
        'ORT-CAS-A0203': {
            'id': 'ORT-CAS-A0203',
            'profile': '21M1V2-',
            'name': 'Vorlen',
            'region': 'ORT',
            'sector': 'CAS-01',
            'subsector': 'A',
            'col': '02',
            'row': '03',
            'ni': '',
            'nr': '',
            'notes': 'pending-link:ORT-CAS-B0101',
        },
    }

    with tempfile.NamedTemporaryFile(suffix='.tsv', delete=False, mode='w') as f:
        tmp = Path(f.name)

    save_tsv(tmp, sample)
    loaded = load_tsv(tmp)

    assert set(loaded.keys()) == set(sample.keys()), "Loaded IDs don't match"
    for sid in sample:
        for field in TSV_FIELDS:
            assert loaded[sid].get(field, '') == sample[sid].get(field, ''), \
                f"Field {field!r} mismatch for {sid}"

    pending = get_pending_links(loaded)
    assert ('ORT-CAS-A0203', 'ORT-CAS-B0101') in pending

    merged = merge(sample, {'ORT-CAS-A0101': {'id': 'ORT-CAS-A0101', 'name': 'REPLACED'}})
    assert merged['ORT-CAS-A0101']['name'] == 'Kethavar', "Existing entry should win in merge"

    tmp.unlink()
    print("io: all tests passed")
