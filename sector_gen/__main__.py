"""sector_gen - procedural interstellar sector generator."""

import argparse
import sys
from pathlib import Path

from .config import (DEFAULT_DENSITY, DEFAULT_PHONEMES, DEFAULT_SECTOR_NUMBER,
                     SUBSECTOR_LETTERS)
from .coordinates import (build_canonical_id, derive_code, hexes_for_subsector,
                           parse_canonical_id)
from .generator import generate_system
from .io import (confirm_overwrite, load_tsv, merge, save_tsv, write_tsv_stdout)
from .names import load_register
from .network import run_network_pass, resolve_pending_links


# ---------------------------------------------------------------------------
# Shared generation helpers (unchanged)
# ---------------------------------------------------------------------------

def _load_register_safe(name: str) -> dict:
    try:
        return load_register(name)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)


def _generate_subsector(region: str, sector_name: str, sector_number: str,
                         subsector: str, density: str, register: dict) -> dict:
    sector_id = f"{sector_name}-{sector_number}"
    systems = {}
    for cid in hexes_for_subsector(region, sector_name, subsector):
        s = generate_system(cid, sector_id, density=density, register=register)
        if s:
            systems[cid] = s
    systems, _ = run_network_pass(systems)
    return systems


def _generate_sector(region: str, sector_name: str, sector_number: str,
                      density: str, register: dict) -> dict:
    all_systems = {}
    for sub in SUBSECTOR_LETTERS:
        all_systems.update(
            _generate_subsector(region, sector_name, sector_number, sub, density, register)
        )
    resolve_pending_links(all_systems)
    return all_systems


def _output(systems: dict, args) -> None:
    if args.output:
        path = Path(args.output)
        save_tsv(path, systems)
        print(f"Wrote {len(systems)} systems to {path}", file=sys.stderr)
    else:
        write_tsv_stdout(systems)


# ---------------------------------------------------------------------------
# Code-derivation helpers
# ---------------------------------------------------------------------------

def _extract_existing_codes(systems: dict) -> tuple:
    """Return (region_code_set, {sector_code: set_of_region_codes}) from a TSV."""
    region_codes: set = set()
    sector_code_map: dict = {}
    for s in systems.values():
        r = s.get('region', '').strip()
        sec = s.get('sector', '').strip()
        sec_code = sec.split('-')[0] if '-' in sec else sec
        if r:
            region_codes.add(r)
        if sec_code:
            sector_code_map.setdefault(sec_code, set()).add(r)
    return region_codes, sector_code_map


def _derive_region_code(region_name: str, existing_codes: set) -> str:
    """Derive region code from a human name; exits on unresolvable collision."""
    try:
        return derive_code(region_name, existing_codes)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)


def _derive_sector_code(sector_name: str, existing_codes: set) -> str:
    """Derive sector code from a human name; exits on unresolvable collision."""
    try:
        return derive_code(sector_name, existing_codes)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)


# ---------------------------------------------------------------------------
# --id parsing helpers (local forms used by generate and build)
# ---------------------------------------------------------------------------

def _parse_subsector_letter(id_arg: str | None) -> str:
    """Accept a bare subsector letter (A-P), case-insensitive."""
    if not id_arg:
        print("error: --id (subsector letter, e.g. A) is required for scope=subsector",
              file=sys.stderr)
        sys.exit(1)
    letter = id_arg.strip().upper()
    if letter in SUBSECTOR_LETTERS:
        return letter
    print(
        f"error: {id_arg!r} is not a valid subsector letter. Expected one of A-P",
        file=sys.stderr,
    )
    sys.exit(1)


def _parse_system_local_id(id_arg: str | None, region_code: str,
                            sector_code: str, sector_number: str) -> tuple:
    """Parse system --id.

    Accepts either a local 'LXXYY' (e.g. C0304) or a full canonical ID.
    Returns (canonical_id, sector_id).
    """
    if not id_arg:
        print("error: --id is required for scope=system (e.g. C0304 or ORT-CAS-C0304)",
              file=sys.stderr)
        sys.exit(1)

    local = id_arg.strip()

    # Full canonical format
    try:
        parts = parse_canonical_id(local)
        sector_id = f"{parts['sector_name']}-{sector_number}"
        return local, sector_id
    except ValueError:
        pass

    # Local format: LXXYY (5 chars)
    if (len(local) == 5
            and local[0].upper() in SUBSECTOR_LETTERS
            and local[1:3].isdigit()
            and local[3:5].isdigit()):
        sub = local[0].upper()
        col, row = int(local[1:3]), int(local[3:5])
        cid = build_canonical_id(region_code, sector_code, sub, col, row)
        return cid, f"{sector_code}-{sector_number}"

    print(
        f"error: cannot parse system ID {id_arg!r}. "
        f"Expected local form LXXYY (e.g. C0304) or full canonical ID (e.g. ORT-CAS-C0304)",
        file=sys.stderr,
    )
    sys.exit(1)


# ---------------------------------------------------------------------------
# Command: generate
# ---------------------------------------------------------------------------

def cmd_generate(args) -> None:
    register = _load_register_safe(args.phonemes)
    scope = args.scope
    density = args.density

    # Load optional input TSV for code-collision checking
    existing_systems: dict = {}
    if args.input:
        in_path = Path(args.input)
        if not in_path.exists():
            print(f"error: input file not found: {in_path}", file=sys.stderr)
            sys.exit(1)
        existing_systems = load_tsv(in_path)

    existing_region_codes, existing_sector_code_map = _extract_existing_codes(existing_systems)
    existing_sector_codes = set(existing_sector_code_map.keys())

    # Derive region code (required for all scopes)
    region_code = _derive_region_code(args.region_name, existing_region_codes)

    # Derive sector code (required for sector / subsector / system)
    sector_code = sector_number = None
    if scope != 'region':
        if not args.sector_name:
            print("error: --sector-name is required for scope != region", file=sys.stderr)
            sys.exit(1)
        sector_code = _derive_sector_code(args.sector_name, existing_sector_codes)
        sector_number = f"{args.sector_index:02d}"

    # --- region ---
    if scope == 'region':
        n = args.sectors
        all_systems: dict = {}
        used_sector_codes = set(existing_sector_codes)
        for i in range(n):
            auto_name = f"Sector{i + 1:02d}"
            try:
                sc = derive_code(auto_name, used_sector_codes)
            except ValueError:
                sc = f"X{i + 1:03d}"[:4]
            used_sector_codes.add(sc)
            all_systems.update(_generate_sector(region_code, sc, '01', density, register))
        resolve_pending_links(all_systems)
        _output(all_systems, args)
        return

    # --- sector ---
    if scope == 'sector':
        systems = _generate_sector(region_code, sector_code, sector_number, density, register)
        _output(systems, args)
        return

    # --- subsector ---
    if scope == 'subsector':
        sub = _parse_subsector_letter(args.id)
        systems = _generate_subsector(region_code, sector_code, sector_number, sub,
                                       density, register)
        _output(systems, args)
        return

    # --- system ---
    if scope == 'system':
        cid, sector_id = _parse_system_local_id(args.id, region_code, sector_code, sector_number)
        s = generate_system(cid, sector_id, density=density, register=register)
        if not s:
            print(f"Empty hex: {cid}", file=sys.stderr)
            sys.exit(0)
        systems = {cid: s}
        systems, _ = run_network_pass(systems)
        _output(systems, args)


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

    # Derive codes without exclusion — for build, the same code appearing in the
    # file is expected (we're extending an existing entity, not creating a new one).
    _, existing_sector_code_map = _extract_existing_codes(existing)

    region_code = _derive_region_code(args.region_name, set())

    if not args.sector_name:
        print("error: --sector-name is required for build", file=sys.stderr)
        sys.exit(1)
    sector_code = _derive_sector_code(args.sector_name, set())

    # Collision check: sector code already in file under a *different* region
    if sector_code in existing_sector_code_map:
        regions_using_code = existing_sector_code_map[sector_code]
        if region_code not in regions_using_code:
            other = sorted(regions_using_code)[0]
            print(
                f"error: sector name {args.sector_name!r} derives code {sector_code!r}, "
                f"which already exists in the file under region {other!r} (not {region_code!r}). "
                f"Please rename to avoid the conflict.",
                file=sys.stderr,
            )
            sys.exit(1)

    sector_number = f"{args.sector_index:02d}"

    if scope == 'sector':
        new_systems = _generate_sector(region_code, sector_code, sector_number, density, register)
    elif scope == 'subsector':
        sub = _parse_subsector_letter(args.id)
        new_systems = _generate_subsector(region_code, sector_code, sector_number, sub,
                                           density, register)
    elif scope == 'system':
        cid, sector_id = _parse_system_local_id(args.id, region_code, sector_code, sector_number)
        s = generate_system(cid, sector_id, density=density, register=register)
        new_systems = {cid: s} if s else {}
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
    from .names import generate_name

    rng = random.Random(seed)
    hz = step_1_hz(rng)
    rx = step_2_rx(hz, rng)
    pp = step_3_pp(hz, rng)
    pw = step_4_pw(pp, rng)
    ac = step_5_ac(hz, pw, rng)
    tn = step_6_tn(pp, pw, rx, rng)
    dx = step_7_dx(hz, rx, rng)
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
    gen.add_argument('--region-name', required=True, dest='region_name',
                     help='Human-readable region name; a code is derived automatically '
                          '(e.g. "Orion Terminus" → ORT)')
    gen.add_argument('--sector-name', default=None, dest='sector_name',
                     help='Human-readable sector name (required for sector/subsector/system scopes)')
    gen.add_argument('--sector-index', type=int, default=1, dest='sector_index',
                     help='Sector number within its region (default: 1)')
    gen.add_argument('--id', default=None,
                     help='For subsector scope: subsector letter (e.g. A). '
                          'For system scope: LXXYY (e.g. C0304) or full canonical ID.')
    gen.add_argument('--sectors', type=int, default=4,
                     help='Number of sectors to generate (region scope only)')
    gen.add_argument('--density', default=DEFAULT_DENSITY,
                     choices=['sparse', 'standard', 'dense', 'cluster'])
    gen.add_argument('--phonemes', default=DEFAULT_PHONEMES,
                     help='Phoneme register name (default, angular, liquid, eastern)')
    gen.add_argument('--input', default=None,
                     help='Existing TSV to check for code collisions before generating')
    gen.add_argument('--output', default=None, help='TSV output path (default: stdout)')

    # ---- build ----
    bld = sub.add_parser('build', help='Extend an existing TSV with new systems')
    bld.add_argument('--input', required=True, help='Existing TSV file')
    bld.add_argument('--scope', required=True,
                     choices=['sector', 'subsector', 'system'])
    bld.add_argument('--region-name', required=True, dest='region_name',
                     help='Human-readable region name; code is derived and collision-checked')
    bld.add_argument('--sector-name', required=True, dest='sector_name',
                     help='Human-readable sector name; code is derived and collision-checked')
    bld.add_argument('--sector-index', type=int, default=1, dest='sector_index',
                     help='Sector number within its region (default: 1)')
    bld.add_argument('--id', default=None,
                     help='For subsector scope: subsector letter. '
                          'For system scope: LXXYY or full canonical ID.')
    bld.add_argument('--density', default=DEFAULT_DENSITY,
                     choices=['sparse', 'standard', 'dense', 'cluster'])
    bld.add_argument('--phonemes', default=DEFAULT_PHONEMES)
    bld.add_argument('--output', default=None,
                     help='Output path (default: overwrite input)')

    # ---- reroll ----
    rrl = sub.add_parser('reroll', help='Reroll a single system')
    rrl.add_argument('--input', required=True)
    rrl.add_argument('--id', required=True, help='Full canonical ID of the system to reroll')
    rrl.add_argument('--reroll-index', type=int, default=1, dest='reroll_index',
                     help='Integer suffix for the reroll seed (default: 1)')
    rrl.add_argument('--phonemes', default=DEFAULT_PHONEMES)
    rrl.add_argument('--output', default=None)

    # ---- render ----
    rnd = sub.add_parser('render', help='Render a scope to SVG')
    rnd.add_argument('--input', required=True)
    rnd.add_argument('--scope', required=True, choices=['subsector', 'sector', 'region'])
    rnd.add_argument('--id', required=True,
                     help='Scope ID passed to the renderer (e.g. ORT-CAS-01-A for subsector)')
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
