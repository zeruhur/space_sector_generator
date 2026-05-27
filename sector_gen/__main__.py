"""sector_gen - procedural interstellar sector generator."""

import argparse
import sys
from pathlib import Path

from .config import (DEFAULT_DENSITY, DEFAULT_PHONEMES, DEFAULT_REGION,
                     DEFAULT_SECTOR_NUMBER, SUBSECTOR_LETTERS)
from .coordinates import (build_canonical_id, hexes_for_sector,
                           hexes_for_subsector, parse_canonical_id)
from .generator import generate_system
from .io import (confirm_overwrite, get_pending_links, load_tsv, merge,
                 save_tsv, write_tsv_stdout)
from .names import load_register
from .network import run_network_pass, resolve_pending_links


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _load_register_safe(name: str) -> dict:
    try:
        return load_register(name)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)


def _parse_system_id(arg: str) -> dict:
    try:
        return parse_canonical_id(arg)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)


def _generate_subsector(region: str, sector_name: str, sector_number: str,
                         subsector: str, density: str, register: dict) -> dict:
    sector_id = f"{sector_name}-{sector_number}"
    hex_ids = hexes_for_subsector(region, sector_name, subsector)
    systems = {}
    for cid in hex_ids:
        s = generate_system(cid, sector_id, density=density, register=register)
        if s:
            systems[cid] = s
    systems, _ = run_network_pass(systems)
    return systems


def _generate_sector(region: str, sector_name: str, sector_number: str,
                      density: str, register: dict) -> dict:
    all_systems = {}
    for sub in SUBSECTOR_LETTERS:
        sub_systems = _generate_subsector(region, sector_name, sector_number,
                                          sub, density, register)
        all_systems.update(sub_systems)
    # Resolve any cross-subsector pending links now that all subsectors exist
    resolve_pending_links(all_systems)
    return all_systems


# ---------------------------------------------------------------------------
# Command: generate
# ---------------------------------------------------------------------------

def cmd_generate(args) -> None:
    register = _load_register_safe(args.phonemes)
    scope = args.scope
    density = args.density

    if scope == 'region':
        n = args.sectors
        import math
        # Lay out N sectors in a grid, auto-assign names
        import string
        sector_names = [f"S{i+1:02d}" for i in range(n)]
        region = args.region or DEFAULT_REGION
        all_systems = {}
        for sname in sector_names:
            s_systems = _generate_sector(region, sname, '01', density, register)
            all_systems.update(s_systems)
        resolve_pending_links(all_systems)
        _output(all_systems, args)
        return

    if scope == 'sector':
        sid = args.id
        if not sid:
            print("error: --id is required for scope=sector (e.g. CAS-01)", file=sys.stderr)
            sys.exit(1)
        region, sector_name, sector_number = _split_sector_id(sid, args.region)
        systems = _generate_sector(region, sector_name, sector_number, density, register)
        _output(systems, args)
        return

    if scope == 'subsector':
        sid = args.id
        if not sid:
            print("error: --id is required for scope=subsector (e.g. CAS-01-C)", file=sys.stderr)
            sys.exit(1)
        region, sector_name, sector_number, subsector = _split_subsector_id(sid, args.region)
        systems = _generate_subsector(region, sector_name, sector_number, subsector,
                                       density, register)
        _output(systems, args)
        return

    if scope == 'system':
        sid = args.id
        if not sid:
            print("error: --id is required for scope=system (e.g. ORT-CAS-C0304)", file=sys.stderr)
            sys.exit(1)
        parts = _parse_system_id(sid)
        sector_id = f"{parts['sector_name']}-{DEFAULT_SECTOR_NUMBER}"
        s = generate_system(sid, sector_id, density=density, register=register)
        if not s:
            print(f"Empty hex: {sid}", file=sys.stderr)
            sys.exit(0)
        systems = {sid: s}
        systems, _ = run_network_pass(systems)
        _output(systems, args)


def _output(systems: dict, args) -> None:
    if args.output:
        path = Path(args.output)
        save_tsv(path, systems)
        print(f"Wrote {len(systems)} systems to {path}", file=sys.stderr)
    else:
        write_tsv_stdout(systems)


def _split_sector_id(sid: str, region_arg: str) -> tuple:
    """Parse 'REGION-NAME-NUM', 'REGION-NAME', 'NAME-NUM', or 'NAME'."""
    parts = sid.split('-')
    if len(parts) == 3:
        return parts[0], parts[1], parts[2]
    if len(parts) == 2:
        # Could be REGION-NAME or NAME-NUM
        if parts[1].isdigit():
            region = region_arg or DEFAULT_REGION
            return region, parts[0], parts[1]
        region = region_arg or DEFAULT_REGION
        return region, parts[0], parts[1]
    if len(parts) == 1:
        region = region_arg or DEFAULT_REGION
        return region, parts[0], DEFAULT_SECTOR_NUMBER
    print(f"error: cannot parse sector id {sid!r}", file=sys.stderr)
    sys.exit(1)


def _split_subsector_id(sid: str, region_arg: str) -> tuple:
    """Parse 'REGION-NAME-NUM-LETTER' down to 'NAME-NUM-LETTER'."""
    parts = sid.split('-')
    if len(parts) == 4:
        return parts[0], parts[1], parts[2], parts[3]
    if len(parts) == 3:
        if parts[2].upper() in SUBSECTOR_LETTERS:
            region = region_arg or DEFAULT_REGION
            return region, parts[0], parts[1], parts[2].upper()
        print(f"error: cannot parse subsector id {sid!r}", file=sys.stderr)
        sys.exit(1)
    if len(parts) == 2:
        if parts[1].upper() in SUBSECTOR_LETTERS:
            region = region_arg or DEFAULT_REGION
            return region, parts[0], DEFAULT_SECTOR_NUMBER, parts[1].upper()
    print(f"error: cannot parse subsector id {sid!r}. Expected NAME-NUM-LETTER or REGION-NAME-NUM-LETTER",
          file=sys.stderr)
    sys.exit(1)


# ---------------------------------------------------------------------------
# Command: build
# ---------------------------------------------------------------------------

def cmd_build(args) -> None:
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"error: input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    existing = load_tsv(input_path)
    register = _load_register_safe(args.phonemes)
    scope = args.scope
    density = args.density
    sid = args.id

    if scope == 'sector':
        region, sector_name, sector_number = _split_sector_id(sid, args.region)
        new_systems = _generate_sector(region, sector_name, sector_number, density, register)
    elif scope == 'subsector':
        region, sector_name, sector_number, subsector = _split_subsector_id(sid, args.region)
        new_systems = _generate_subsector(region, sector_name, sector_number, subsector,
                                           density, register)
    elif scope == 'system':
        parts = _parse_system_id(sid)
        sector_id = f"{parts['sector_name']}-{DEFAULT_SECTOR_NUMBER}"
        s = generate_system(sid, sector_id, density=density, register=register)
        new_systems = {sid: s} if s else {}
        if new_systems:
            new_systems, _ = run_network_pass(new_systems)
    else:
        print(f"error: unsupported scope for build: {scope!r}", file=sys.stderr)
        sys.exit(1)

    merged = merge(existing, new_systems)
    resolve_pending_links(merged)

    output_path = Path(args.output) if args.output else input_path
    if output_path == input_path and output_path.exists():
        if not confirm_overwrite(output_path):
            print("Aborted.", file=sys.stderr)
            sys.exit(0)

    save_tsv(output_path, merged)
    added = len(merged) - len(existing)
    print(f"Merged: {len(existing)} existing + {added} new = {len(merged)} total systems",
          file=sys.stderr)
    print(f"Wrote {output_path}", file=sys.stderr)


# ---------------------------------------------------------------------------
# Command: reroll
# ---------------------------------------------------------------------------

def cmd_reroll(args) -> None:
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"error: input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    systems = load_tsv(input_path)
    sid = args.id
    if sid not in systems:
        print(f"error: system {sid!r} not found in {input_path}", file=sys.stderr)
        sys.exit(1)

    n = args.reroll_index
    seed = sid + f"-reroll{n}"
    old = systems[sid]
    register = _load_register_safe(args.phonemes)

    import random
    from .generator import (step_1_hz, step_2_rx, step_3_pp, step_4_pw,
                             step_5_ac, step_6_tn, step_7_dx, build_profile)
    rng = random.Random(seed)
    hz = step_1_hz(rng)
    rx = step_2_rx(hz, rng)
    pp = step_3_pp(hz, rng)
    pw = step_4_pw(pp, rng)
    ac = step_5_ac(hz, pw, rng)
    tn = step_6_tn(pp, pw, rx, rng)
    dx = step_7_dx(hz, rx, rng)
    name = load_register(args.phonemes)
    from .names import generate_name
    new_name = generate_name(register, seed + '-name')

    systems[sid] = dict(old)
    systems[sid].update({
        'profile': build_profile(ac, hz, rx, pp, pw, tn, dx),
        'name': new_name,
        'ni': '',
        'nr': '',
        '_ac': ac, '_hz': hz, '_rx': rx, '_pp': pp, '_pw': pw, '_tn': tn, '_dx': dx,
        '_col': int(old['col']), '_row': int(old['row']),
    })

    # Re-run network pass for the affected subsector
    sub = old['subsector']
    sub_systems = {k: v for k, v in systems.items() if v.get('subsector') == sub}
    sub_systems, _ = run_network_pass(sub_systems)
    systems.update(sub_systems)

    output_path = Path(args.output) if args.output else input_path
    if output_path == input_path:
        if not confirm_overwrite(output_path):
            print("Aborted.", file=sys.stderr)
            sys.exit(0)

    save_tsv(output_path, systems)
    print(f"Rerolled {sid} (reroll index {n}), wrote {output_path}", file=sys.stderr)


# ---------------------------------------------------------------------------
# Command: render
# ---------------------------------------------------------------------------

def cmd_render(args) -> None:
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"error: input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    systems = load_tsv(input_path)
    output_path = Path(args.output)

    from .renderer import render
    try:
        render(systems, args.scope, args.id, output_path,
               show_profile=args.show_profile, color=args.color)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Rendered {args.scope} {args.id!r} to {output_path}", file=sys.stderr)


# ---------------------------------------------------------------------------
# Command: test
# ---------------------------------------------------------------------------

def cmd_test(_args) -> None:
    print("Running tests…")
    from .coordinates import test as test_coordinates
    from .names import test as test_names
    from .generator import test as test_generator
    from .network import test as test_network
    from .io import test as test_io

    test_coordinates()
    test_names()
    test_generator()
    test_network()
    test_io()
    print("All tests passed.")


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog='python -m sector_gen',
        description='Procedural interstellar sector generator for tabletop RPGs.',
    )
    sub = parser.add_subparsers(dest='command', required=True)

    # ---- generate ----
    gen = sub.add_parser('generate', help='Generate a new sector/subsector/system')
    gen.add_argument('--scope', required=True,
                     choices=['region', 'sector', 'subsector', 'system'])
    gen.add_argument('--id', default=None,
                     help='Canonical ID (required for sector/subsector/system scopes)')
    gen.add_argument('--region', default=None,
                     help='2-4 letter region code (used when scope is sector/subsector)')
    gen.add_argument('--sectors', type=int, default=4,
                     help='Number of sectors to generate (region scope only)')
    gen.add_argument('--density', default=DEFAULT_DENSITY,
                     choices=['sparse', 'standard', 'dense', 'cluster'])
    gen.add_argument('--phonemes', default=DEFAULT_PHONEMES,
                     help='Phoneme register name (default, angular, liquid, eastern)')
    gen.add_argument('--output', default=None, help='TSV output path (default: stdout)')

    # ---- build ----
    bld = sub.add_parser('build', help='Extend an existing TSV with new systems')
    bld.add_argument('--input', required=True, help='Existing TSV file')
    bld.add_argument('--scope', required=True,
                     choices=['sector', 'subsector', 'system'])
    bld.add_argument('--id', required=True)
    bld.add_argument('--region', default=None)
    bld.add_argument('--density', default=DEFAULT_DENSITY,
                     choices=['sparse', 'standard', 'dense', 'cluster'])
    bld.add_argument('--phonemes', default=DEFAULT_PHONEMES)
    bld.add_argument('--output', default=None,
                     help='Output path (default: overwrite input)')

    # ---- reroll ----
    rrl = sub.add_parser('reroll', help='Reroll a single system')
    rrl.add_argument('--input', required=True)
    rrl.add_argument('--id', required=True, help='Canonical ID of the system to reroll')
    rrl.add_argument('--reroll-index', type=int, default=1,
                     dest='reroll_index',
                     help='Integer suffix for the reroll seed (default: 1)')
    rrl.add_argument('--phonemes', default=DEFAULT_PHONEMES)
    rrl.add_argument('--output', default=None)

    # ---- render ----
    rnd = sub.add_parser('render', help='Render a scope to SVG')
    rnd.add_argument('--input', required=True)
    rnd.add_argument('--scope', required=True, choices=['subsector', 'sector', 'region'])
    rnd.add_argument('--id', required=True,
                     help='Scope ID (e.g. ORT-CAS-01-C for subsector, ORT-CAS-01 for sector)')
    rnd.add_argument('--output', required=True, help='Output SVG path')
    rnd.add_argument('--show-profile', action='store_true', dest='show_profile')
    rnd.add_argument('--color', action='store_true')

    # ---- test ----
    sub.add_parser('test', help='Run built-in tests')

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    dispatch = {
        'generate': cmd_generate,
        'build': cmd_build,
        'reroll': cmd_reroll,
        'render': cmd_render,
        'test': cmd_test,
    }
    dispatch[args.command](args)


if __name__ == '__main__':
    main()
