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


def export_markdown(path: Path, systems: dict) -> None:
    """Export all systems to a Markdown file with an index and detailed sheets."""
    from .viewer import translate_system, translate_profile_dict
    
    with path.open('w', encoding='utf-8') as f:
        f.write("# 🌌 Sector Report\n\n")
        
        # 1. Summary Index Table
        f.write("## 📊 System Index\n\n")
        f.write("| System | Profile | Access | Hazard | Resources | Population | Power | Tension | Distinct | Network |\n")
        f.write("| :--- | :---: | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |\n")
        
        for sid in sorted(systems.keys()):
            s = systems[sid]
            t = translate_profile_dict(s['profile'])
            if "error" in t: continue
            
            # Short versions for the table
            ac = t['access'].split(' - ')[0].split(' (')[0]
            hz = t['hazard'].split(' (')[0]
            rx = t['resources'].split(': ')[0].split(' / ')[0]
            pp = t['population'].split(' - ')[0]
            pw = t['power'].split(' - ')[0]
            tn = t['tension'].split(' - ')[0].split(', ')[0]
            dx = t['distinctiveness'].split(' - ')[0]
            net = f"{t['net_importance'].split(' - ')[0]} ({t['net_role'].split(' - ')[0]})" if t['net_importance'] else "-"
            
            f.write(f"| **{s['name']}** | `{s['profile']}` | {ac} | {hz} | {rx} | {pp} | {pw} | {tn} | {dx} | {net} |\n")
            
        f.write("\n---\n\n## 🪐 System Detail Sheets\n\n")
        
        # 2. Detailed Sheets
        for sid in sorted(systems.keys()):
            f.write(translate_system(systems[sid]))
            f.write("\n\n---\n\n")


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
