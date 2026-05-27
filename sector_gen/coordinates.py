import re

from .config import SUBSECTOR_COLS, SUBSECTOR_ROWS, SUBSECTOR_LETTERS

# Format: REGION-SECTORNAME-LXXYY  e.g. ORT-CAS-C0304
CANONICAL_ID_RE = re.compile(r'^([A-Z]{2,4})-([A-Z]{2,4})-([A-P])(\d{2})(\d{2})$')


def parse_canonical_id(cid: str) -> dict:
    m = CANONICAL_ID_RE.match(cid)
    if not m:
        raise ValueError(
            f"Invalid canonical ID {cid!r}. Expected REGION-SECTOR-LXXYY (e.g. ORT-CAS-C0304)"
        )
    region, sector_name, subsector, col_s, row_s = m.groups()
    col, row = int(col_s), int(row_s)
    if not (1 <= col <= SUBSECTOR_COLS):
        raise ValueError(f"Column {col:02d} out of range 01-{SUBSECTOR_COLS:02d} in {cid!r}")
    if not (1 <= row <= SUBSECTOR_ROWS):
        raise ValueError(f"Row {row:02d} out of range 01-{SUBSECTOR_ROWS:02d} in {cid!r}")
    return {
        'region': region,
        'sector_name': sector_name,
        'subsector': subsector,
        'col': col,
        'row': row,
    }


def build_canonical_id(region: str, sector_name: str, subsector: str, col: int, row: int) -> str:
    return f"{region}-{sector_name}-{subsector}{col:02d}{row:02d}"


def hex_distance(col1: int, row1: int, col2: int, row2: int) -> int:
    # Odd-offset columns: odd-numbered columns shift down by half a hex.
    # This matches the column-offset convention used in the rendering module.
    def to_cube(col, row):
        x = col
        z = row - (col - (col & 1)) // 2
        y = -x - z
        return x, y, z

    x1, y1, z1 = to_cube(col1, row1)
    x2, y2, z2 = to_cube(col2, row2)
    return max(abs(x1 - x2), abs(y1 - y2), abs(z1 - z2))


def is_subsector_edge(col: int, row: int) -> bool:
    return col == 1 or col == SUBSECTOR_COLS or row == 1 or row == SUBSECTOR_ROWS


def hexes_for_subsector(region: str, sector_name: str, subsector: str) -> list:
    return [
        build_canonical_id(region, sector_name, subsector, c, r)
        for c in range(1, SUBSECTOR_COLS + 1)
        for r in range(1, SUBSECTOR_ROWS + 1)
    ]


def hexes_for_sector(region: str, sector_name: str) -> list:
    ids = []
    for s in SUBSECTOR_LETTERS:
        ids.extend(hexes_for_subsector(region, sector_name, s))
    return ids


def subsector_index(letter: str) -> tuple:
    """Return (col_index, row_index) of a subsector within its sector (0-based)."""
    idx = SUBSECTOR_LETTERS.index(letter)
    return idx % SECTOR_SUBSECTORS_WIDE, idx // SECTOR_SUBSECTORS_WIDE


def test():
    assert hex_distance(1, 1, 1, 1) == 0, "self-distance should be 0"
    assert hex_distance(3, 5, 1, 1) == hex_distance(1, 1, 3, 5), "distance must be symmetric"
    assert hex_distance(1, 1, 2, 1) == 1, "adjacent columns should be distance 1"
    assert hex_distance(1, 1, 1, 2) == 1, "adjacent rows should be distance 1"

    cid = build_canonical_id('ORT', 'CAS', 'C', 3, 4)
    assert cid == 'ORT-CAS-C0304'
    parts = parse_canonical_id(cid)
    assert parts['region'] == 'ORT'
    assert parts['sector_name'] == 'CAS'
    assert parts['subsector'] == 'C'
    assert parts['col'] == 3
    assert parts['row'] == 4

    assert is_subsector_edge(1, 5)
    assert is_subsector_edge(8, 5)
    assert is_subsector_edge(4, 1)
    assert is_subsector_edge(4, 10)
    assert not is_subsector_edge(4, 5)

    hexes = hexes_for_subsector('ORT', 'CAS', 'A')
    assert len(hexes) == SUBSECTOR_COLS * SUBSECTOR_ROWS
    assert hexes[0] == 'ORT-CAS-A0101'

    print("coordinates: all tests passed")
