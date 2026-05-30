import random

from .config import DENSITY_THRESHOLDS
from .coordinates import parse_canonical_id


# ---------------------------------------------------------------------------
# Step helpers
# ---------------------------------------------------------------------------

def _roll2d6(rng: random.Random) -> int:
    return rng.randint(1, 6) + rng.randint(1, 6)


def _roll1d6(rng: random.Random) -> int:
    return rng.randint(1, 6)


# ---------------------------------------------------------------------------
# Step 0 - Presence check
# ---------------------------------------------------------------------------

def step_0_presence(density: str, rng: random.Random) -> bool:
    threshold = DENSITY_THRESHOLDS[density]
    return _roll1d6(rng) >= threshold


# ---------------------------------------------------------------------------
# Step 1 - Hz (Hazard)
# ---------------------------------------------------------------------------

def step_1_hz(rng: random.Random) -> int:
    roll = _roll2d6(rng)
    if roll == 2:
        return 5
    elif roll <= 4:
        return 4
    elif roll <= 6:
        return 3
    elif roll <= 9:
        return 2
    elif roll <= 11:
        return 1
    else:
        return 0


# ---------------------------------------------------------------------------
# Step 2 - Rx (Resource)
# ---------------------------------------------------------------------------

_RX_TABLE = {
    2: 'N', 3: 'B', 4: 'T', 5: 'T', 6: 'M', 7: 'M', 8: 'M',
    9: 'I', 10: 'C', 11: 'S', 12: 'X',
}


def step_2_rx(hz: int, rng: random.Random) -> str:
    roll = _roll2d6(rng)
    rx = _RX_TABLE[roll]
    if hz >= 4 and rx in ('T', 'I', 'B'):
        rx = 'M'
    return rx


# ---------------------------------------------------------------------------
# Step 3 - Pp (Population potential)
# ---------------------------------------------------------------------------

def step_3_pp(hz: int, rng: random.Random) -> int:
    roll = _roll2d6(rng) - hz
    if roll <= 3:
        pp = 0
    elif roll <= 5:
        pp = 1
    elif roll <= 7:
        pp = 2
    elif roll <= 9:
        pp = 3
    elif roll <= 11:
        pp = 4
    else:
        pp = 5
    if hz == 5:
        pp = min(pp, 1)
    elif hz == 4:
        pp = min(pp, 2)
    return pp


# ---------------------------------------------------------------------------
# Step 4 - Pw (Population wealth)
# ---------------------------------------------------------------------------

_PW_TABLES = {
    # (roll_min, roll_max, result)
    0: [(1, 6, 'V')],
    1: [(1, 2, 'V'), (3, 4, 'A'), (5, 6, 'E')],
    2: [(1, 1, 'A'), (2, 3, 'L'), (4, 4, 'C'), (5, 5, 'E'), (6, 6, 'A')],
    3: [(1, 1, 'A'), (2, 3, 'L'), (4, 4, 'C'), (5, 5, 'S'), (6, 6, 'E')],
    4: [(1, 1, 'L'), (2, 3, 'C'), (4, 5, 'S'), (6, 6, 'H')],
    5: [(1, 1, 'C'), (2, 3, 'S'), (4, 5, 'H'), (6, 6, 'E')],
}


def step_4_pw(pp: int, rng: random.Random) -> str:
    if pp == 0:
        return 'V'
    roll = _roll1d6(rng)
    for lo, hi, result in _PW_TABLES[pp]:
        if lo <= roll <= hi:
            return result
    return 'V'  # unreachable but safe


# ---------------------------------------------------------------------------
# Step 5 - Ac (Access)
# ---------------------------------------------------------------------------

_AC_MOD_HZ = {1: -1, 2: -1, 3: -2, 4: -2, 5: -3}
_AC_MOD_PW = {'V': -2, 'A': -1, 'L': 0, 'C': 1, 'E': 1, 'S': 0, 'H': 2}


def step_5_ac(hz: int, pw: str, rng: random.Random) -> int:
    roll = _roll2d6(rng)
    mod = _AC_MOD_HZ.get(hz, 0) + _AC_MOD_PW.get(pw, 0)
    modified = roll + mod
    if modified >= 12:
        return 0
    elif modified >= 10:
        return 1
    elif modified >= 8:
        return 2
    elif modified >= 6:
        return 3
    elif modified >= 4:
        return 4
    else:
        return 5


# ---------------------------------------------------------------------------
# Step 6 - Tn (Technology/Trade network)
# ---------------------------------------------------------------------------

_TN_MOD_PP = {0: -3, 1: -1, 2: -1, 3: 0, 4: 1, 5: 2}
_TN_MOD_PW = {'V': -2, 'A': 2, 'L': 0, 'C': 0, 'E': 0, 'S': 0, 'H': 1}


def step_6_tn(pp: int, pw: str, rx: str, rng: random.Random) -> int:
    roll = _roll2d6(rng)
    mod = _TN_MOD_PP.get(pp, 0) + _TN_MOD_PW.get(pw, 0)
    if rx == 'S':
        mod += 1
    modified = roll + mod
    if modified <= 3:
        return 0
    elif modified <= 5:
        return 1
    elif modified <= 7:
        return 2
    elif modified <= 9:
        return 3
    elif modified <= 11:
        return 4
    else:
        return 5


# ---------------------------------------------------------------------------
# Step 7 - Dx (Distinguishing feature)
# ---------------------------------------------------------------------------

_DX_SUBTABLE = {1: 'X', 2: 'P', 3: 'H', 5: 'R', 6: 'W'}
_DX_FOR_X_RX = {1: 'P', 2: 'P', 3: 'X', 4: 'X', 5: 'H', 6: 'H'}


def step_7_dx(hz: int, rx: str, rng: random.Random) -> str:
    if rx == 'X':
        return _DX_FOR_X_RX[_roll1d6(rng)]

    roll1 = _roll1d6(rng)
    if roll1 <= 2:
        if hz >= 4:
            roll1 = _roll1d6(rng)  # one reroll if high hazard
            if roll1 <= 2:
                return '-'
        else:
            return '-'

    roll2 = _roll1d6(rng)
    if roll2 == 4:
        return 'T' if _roll1d6(rng) <= 3 else 'C'
    return _DX_SUBTABLE[roll2]


# ---------------------------------------------------------------------------
# Profile helpers
# ---------------------------------------------------------------------------

def build_profile(ac: int, hz: int, rx: str, pp: int, pw: str, tn: int, dx: str,
                  ni='', nr='') -> str:
    base = f"{ac}{hz}{rx}{pp}{pw}{tn}{dx}"
    if ni != '' and nr != '':
        return f"{base}-{ni}{nr}"
    return base


def parse_profile(profile: str) -> dict:
    """Parse a stored profile string back to raw field values."""
    if len(profile) == 10 and profile[7] == '-':
        base = profile[:7]
        net = profile[8:]
        ni = int(net[0])
        nr = net[1]
    elif len(profile) == 7:
        base = profile
        ni = ''
        nr = ''
    else:
        raise ValueError(f"Unrecognised profile format: {profile!r}")
    return {
        'ac': int(base[0]),
        'hz': int(base[1]),
        'rx': base[2],
        'pp': int(base[3]),
        'pw': base[4],
        'tn': int(base[5]),
        'dx': base[6],
        'ni': ni,
        'nr': nr,
    }


# ---------------------------------------------------------------------------
# Top-level generation
# ---------------------------------------------------------------------------

def generate_system(canonical_id: str, sector_id: str, density: str = 'standard',
                    register: dict = None, expanded: bool = False) -> dict | None:
    """Generate a single system. Returns None if the hex is empty."""
    rng = random.Random(canonical_id)

    if not step_0_presence(density, rng):
        return None

    parts = parse_canonical_id(canonical_id)

    hz = step_1_hz(rng)
    rx = step_2_rx(hz, rng)
    pp = step_3_pp(hz, rng)
    pw = step_4_pw(pp, rng)
    ac = step_5_ac(hz, pw, rng)
    tn = step_6_tn(pp, pw, rx, rng)
    dx = step_7_dx(hz, rx, rng)

    from .names import generate_name
    name = generate_name(register, canonical_id) if register else canonical_id

    system = {
        'id': canonical_id,
        'profile': build_profile(ac, hz, rx, pp, pw, tn, dx),
        'name': name,
        'region': parts['region'],
        'sector': sector_id,
        'subsector': parts['subsector'],
        'col': f"{parts['col']:02d}",
        'row': f"{parts['row']:02d}",
        'ni': '',
        'nr': '',
        'notes': '',
        'expansion': '',
        # Raw fields for the network pass (not written to TSV)
        '_ac': ac,
        '_hz': hz,
        '_rx': rx,
        '_pp': pp,
        '_pw': pw,
        '_tn': tn,
        '_dx': dx,
        '_col': parts['col'],
        '_row': parts['row'],
    }

    if expanded:
        from .expansion import expand_system
        system['expansion'] = expand_system(system)

    return system


def ensure_raw_fields(system: dict) -> dict:
    """Populate _ac … _col/_row from stored profile if they are missing."""
    if '_ac' in system:
        return system
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
    return system


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test():
    from .coordinates import build_canonical_id
    from .names import load_register

    register = load_register('default')
    valid_rx = set('NBTMICSX')
    valid_pw = set('VALCSEH')
    valid_dx = set('-XPHTCRW')

    passed = failed = 0
    for i in range(100):
        cid = build_canonical_id('TST', 'GEN', 'A', (i % 8) + 1, (i % 10) + 1)
        s = generate_system(cid, 'GEN-01', density='standard', register=register)
        if s is None:
            continue
        try:
            assert 0 <= s['_hz'] <= 5, f"Hz out of range: {s['_hz']}"
            assert s['_rx'] in valid_rx, f"Rx invalid: {s['_rx']}"
            assert 0 <= s['_pp'] <= 5, f"Pp out of range: {s['_pp']}"
            assert s['_pw'] in valid_pw, f"Pw invalid: {s['_pw']}"
            assert 0 <= s['_ac'] <= 5, f"Ac out of range: {s['_ac']}"
            assert 0 <= s['_tn'] <= 5, f"Tn out of range: {s['_tn']}"
            assert s['_dx'] in valid_dx, f"Dx invalid: {s['_dx']}"
            assert s['name'], "Name is empty"
            passed += 1
        except AssertionError as e:
            print(f"FAIL {cid}: {e}")
            failed += 1

    assert failed == 0, f"{failed} systems failed validation"
    print(f"generator: {passed} systems validated, all tests passed")
