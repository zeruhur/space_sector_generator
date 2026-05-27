from .coordinates import hex_distance, is_subsector_edge, build_canonical_id, parse_canonical_id
from .generator import ensure_raw_fields, build_profile


# ---------------------------------------------------------------------------
# Ni calculation
# ---------------------------------------------------------------------------

_NI_THRESHOLDS = [(2, 0), (5, 1), (8, 2), (10, 3), (12, 4)]


def calc_ni(system: dict) -> int:
    s = ensure_raw_fields(system)
    raw = s['_pp'] + (5 - s['_ac'])
    if s['_rx'] in ('S', 'T'):
        raw += 2
    if s['_pw'] == 'H':
        raw += 2
    if s['_tn'] >= 4:
        raw += 1
    for threshold, ni in _NI_THRESHOLDS:
        if raw <= threshold:
            return ni
    return 5


# ---------------------------------------------------------------------------
# Nr calculation
# ---------------------------------------------------------------------------

def calc_nr(system: dict, conn: int, is_ap: bool) -> str:
    s = ensure_raw_fields(system)
    ac = s['_ac']
    tn = s['_tn']
    pw = s['_pw']
    ni = system.get('_ni', system.get('ni', 0))
    if isinstance(ni, str):
        ni = int(ni) if ni else 0
    edge = is_subsector_edge(s['_col'], s['_row'])

    if conn == 0:
        nr = 'I'
    elif conn == 1 and edge:
        nr = 'F'
    elif conn == 1:
        nr = 'B'
    elif ac >= 3 and tn <= 1 and pw in ('L', 'A'):
        nr = 'S'
    elif conn in (2, 3) and ni <= 2:
        nr = 'T'
    elif conn in (2, 3) and ni >= 3:
        nr = 'H'
    else:
        nr = 'H'

    if is_ap and nr != 'I':
        nr = 'K'
    return nr


# ---------------------------------------------------------------------------
# Articulation point detection (Tarjan, iterative)
# ---------------------------------------------------------------------------

def find_articulation_points(systems: dict) -> set:
    """Return set of system IDs whose removal disconnects the proximity graph."""
    ids = list(systems.keys())
    if len(ids) <= 2:
        return set()

    # Build adjacency on the within-2-hex proximity graph
    adj = {sid: [] for sid in ids}
    for i, sid1 in enumerate(ids):
        s1 = systems[sid1]
        col1, row1 = s1['_col'], s1['_row']
        for sid2 in ids[i + 1:]:
            s2 = systems[sid2]
            if hex_distance(col1, row1, s2['_col'], s2['_row']) <= 2:
                adj[sid1].append(sid2)
                adj[sid2].append(sid1)

    # Iterative Tarjan articulation-point algorithm
    disc = {}
    low = {}
    parent = {sid: None for sid in ids}
    ap = set()
    timer = [0]

    for start in ids:
        if start in disc:
            continue
        stack = [(start, iter(adj[start]))]
        disc[start] = low[start] = timer[0]
        timer[0] += 1

        while stack:
            u, children = stack[-1]
            try:
                v = next(children)
                if v not in disc:
                    parent[v] = u
                    disc[v] = low[v] = timer[0]
                    timer[0] += 1
                    stack.append((v, iter(adj[v])))
                elif v != parent[u]:
                    low[u] = min(low[u], disc[v])
            except StopIteration:
                stack.pop()
                if stack:
                    p = stack[-1][0]
                    low[p] = min(low[p], low[u])
                    if parent[p] is None:
                        # Root is AP if it has more than one DFS child
                        root_children = sum(1 for v in adj[p] if parent.get(v) == p)
                        if root_children > 1:
                            ap.add(p)
                    elif low[u] >= disc[p]:
                        ap.add(p)

    return ap


# ---------------------------------------------------------------------------
# Route determination
# ---------------------------------------------------------------------------

_DISTANCE_PENALTY = {1: 0, 2: 2, 3: 4}


def _tier_from_score(score: int) -> str | None:
    if score >= 8:
        return 'Primary'
    elif score >= 5:
        return 'Secondary'
    elif score >= 3:
        return 'Tertiary'
    return None


def _upgrade_tier(tier: str | None) -> str | None:
    if tier == 'Tertiary':
        return 'Secondary'
    if tier == 'Secondary':
        return 'Primary'
    return 'Primary'


def _downgrade_tier(tier: str | None) -> str | None:
    if tier == 'Primary':
        return 'Secondary'
    if tier == 'Secondary':
        return 'Tertiary'
    return None  # Tertiary → deactivated


def calc_routes(systems: dict) -> list:
    """Return list of (id1, id2, tier) tuples for all active intra-subsector routes."""
    ids = [sid for sid, s in systems.items() if s.get('nr') != 'I']

    candidates = []
    for i, sid1 in enumerate(ids):
        s1 = systems[sid1]
        ni1 = int(s1.get('_ni', s1.get('ni', 0)) or 0)
        reach1 = 3 if ni1 == 5 else 2
        for sid2 in ids[i + 1:]:
            s2 = systems[sid2]
            ni2 = int(s2.get('_ni', s2.get('ni', 0)) or 0)
            reach2 = 3 if ni2 == 5 else 2
            dist = hex_distance(s1['_col'], s1['_row'], s2['_col'], s2['_row'])
            if dist > max(reach1, reach2):
                continue
            if dist == 3 and not (ni1 == 5 or ni2 == 5):
                continue
            penalty = _DISTANCE_PENALTY.get(dist, 999)
            score = ni1 + ni2 - penalty
            tier = _tier_from_score(score)
            if tier:
                candidates.append([sid1, sid2, tier, score])

    # Pass 1: K endpoints upgrade one tier
    for link in candidates:
        sid1, sid2 = link[0], link[1]
        if systems[sid1].get('nr') == 'K' or systems[sid2].get('nr') == 'K':
            link[2] = _upgrade_tier(link[2])

    # Pass 2: S endpoints downgrade one tier (unless score >= 8)
    active = []
    for sid1, sid2, tier, score in candidates:
        if score < 8 and (systems[sid1].get('nr') == 'S' or systems[sid2].get('nr') == 'S'):
            tier = _downgrade_tier(tier)
        if tier is not None:
            active.append((sid1, sid2, tier))

    return active


# ---------------------------------------------------------------------------
# Cross-subsector pending link detection
# ---------------------------------------------------------------------------

def detect_pending_links(systems: dict, all_subsector_ids: set) -> dict:
    """For each system near a subsector edge, record pending links to adjacent hexes
    not in this subsector. Returns {system_id: [neighbor_canonical_id, ...]}."""
    pending = {}
    for sid, s in systems.items():
        ni = int(s.get('_ni', s.get('ni', 0)) or 0)
        reach = 3 if ni == 5 else 2
        if not is_subsector_edge(s['_col'], s['_row']):
            continue
        parts = parse_canonical_id(sid)
        neighbors = []
        for dc in range(-reach, reach + 1):
            for dr in range(-reach, reach + 1):
                nc, nr_ = s['_col'] + dc, s['_row'] + dr
                if nc < 1 or nr_ < 1:
                    continue
                if hex_distance(s['_col'], s['_row'], nc, nr_) > reach:
                    continue
                # Only care about hexes outside this subsector
                if 1 <= nc <= 8 and 1 <= nr_ <= 10:
                    continue
                # Build the canonical ID for the neighbor in the adjacent subsector
                neighbor_id = _adjacent_subsector_id(parts, nc, nr_)
                if neighbor_id and neighbor_id not in all_subsector_ids:
                    neighbors.append(neighbor_id)
        if neighbors:
            pending[sid] = list(set(neighbors))
    return pending


def _adjacent_subsector_id(parts: dict, abs_col: int, abs_row: int) -> str | None:
    """Convert an out-of-bounds (col, row) relative to a subsector into the canonical
    ID in the adjacent subsector, or None if the coordinates are invalid."""
    from .config import SUBSECTOR_LETTERS, SECTOR_SUBSECTORS_WIDE, SECTOR_SUBSECTORS_TALL, SUBSECTOR_COLS, SUBSECTOR_ROWS
    sub_idx = SUBSECTOR_LETTERS.index(parts['subsector'])
    sub_col_idx = sub_idx % SECTOR_SUBSECTORS_WIDE
    sub_row_idx = sub_idx // SECTOR_SUBSECTORS_WIDE

    # Compute absolute hex position within the sector
    sector_col = sub_col_idx * SUBSECTOR_COLS + abs_col
    sector_row = sub_row_idx * SUBSECTOR_ROWS + abs_row

    if sector_col < 1 or sector_row < 1:
        return None
    max_sector_col = SECTOR_SUBSECTORS_WIDE * SUBSECTOR_COLS
    max_sector_row = SECTOR_SUBSECTORS_TALL * SUBSECTOR_ROWS
    if sector_col > max_sector_col or sector_row > max_sector_row:
        return None

    target_sub_col = (sector_col - 1) // SUBSECTOR_COLS
    target_sub_row = (sector_row - 1) // SUBSECTOR_ROWS
    target_sub_idx = target_sub_row * SECTOR_SUBSECTORS_WIDE + target_sub_col
    target_sub_letter = SUBSECTOR_LETTERS[target_sub_idx]
    target_col = ((sector_col - 1) % SUBSECTOR_COLS) + 1
    target_row = ((sector_row - 1) % SUBSECTOR_ROWS) + 1
    return build_canonical_id(parts['region'], parts['sector_name'], target_sub_letter, target_col, target_row)


# ---------------------------------------------------------------------------
# Full network pass for a subsector
# ---------------------------------------------------------------------------

def run_network_pass(systems: dict) -> tuple:
    """Run the full network pass on a dict of systems in one subsector.

    Returns (updated_systems, routes) where routes is a list of (id1, id2, tier).
    Modifies systems in-place and also returns them for convenience.
    """
    if not systems:
        return systems, []

    # Ensure raw fields are loaded for every system
    for s in systems.values():
        ensure_raw_fields(s)

    # Step 1: Ni
    for sid, s in systems.items():
        ni = calc_ni(s)
        s['_ni'] = ni

    # Step 2: Count within-2-hex neighbors
    ids = list(systems.keys())
    conn_map = {sid: 0 for sid in ids}
    for i, sid1 in enumerate(ids):
        s1 = systems[sid1]
        for sid2 in ids[i + 1:]:
            s2 = systems[sid2]
            if hex_distance(s1['_col'], s1['_row'], s2['_col'], s2['_row']) <= 2:
                conn_map[sid1] += 1
                conn_map[sid2] += 1

    # Step 3: Articulation points
    aps = find_articulation_points(systems)

    # Step 4: Nr
    for sid, s in systems.items():
        nr = calc_nr(s, conn_map[sid], sid in aps)
        s['_nr'] = nr
        s['nr'] = nr

    # Step 5: Finalize Ni and update profile
    for sid, s in systems.items():
        ni = s['_ni']
        s['ni'] = str(ni)
        s['profile'] = build_profile(
            s['_ac'], s['_hz'], s['_rx'], s['_pp'], s['_pw'], s['_tn'], s['_dx'],
            ni, s['nr']
        )

    # Step 6: Routes
    routes = calc_routes(systems)

    # Step 7: Pending cross-subsector links → notes
    all_ids = set(systems.keys())
    pending = detect_pending_links(systems, all_ids)
    for sid, neighbors in pending.items():
        existing = systems[sid].get('notes', '')
        tags = [f"pending-link:{n}" for n in neighbors]
        all_tags = existing.split(';') if existing else []
        # Don't duplicate
        for tag in tags:
            if tag not in all_tags:
                all_tags.append(tag)
        systems[sid]['notes'] = ';'.join(t for t in all_tags if t)

    return systems, routes


# ---------------------------------------------------------------------------
# Cross-subsector link resolution
# ---------------------------------------------------------------------------

def resolve_pending_links(systems: dict) -> list:
    """Score and resolve any pending-link entries in notes whose targets exist
    in the systems dict. Returns list of newly resolved (id1, id2, tier) tuples."""
    resolved = []
    for sid, s in systems.items():
        notes = s.get('notes', '')
        if 'pending-link:' not in notes:
            continue
        parts_notes = [t for t in notes.split(';') if t]
        remaining = []
        for tag in parts_notes:
            if not tag.startswith('pending-link:'):
                remaining.append(tag)
                continue
            target_id = tag[len('pending-link:'):]
            if target_id not in systems:
                remaining.append(tag)
                continue
            # Score the link
            s1 = ensure_raw_fields(s)
            s2 = ensure_raw_fields(systems[target_id])
            ni1 = int(s1.get('_ni', s1.get('ni', 0)) or 0)
            ni2 = int(s2.get('_ni', s2.get('ni', 0)) or 0)
            dist = hex_distance(s1['_col'], s1['_row'], s2['_col'], s2['_row'])
            reach1 = 3 if ni1 == 5 else 2
            reach2 = 3 if ni2 == 5 else 2
            if dist > max(reach1, reach2):
                remaining.append(tag)
                continue
            penalty = _DISTANCE_PENALTY.get(dist, 999)
            score = ni1 + ni2 - penalty
            tier = _tier_from_score(score)
            if tier:
                # Apply K/S modifiers
                nr1 = s.get('nr', s.get('_nr', ''))
                nr2 = systems[target_id].get('nr', '')
                if nr1 == 'K' or nr2 == 'K':
                    tier = _upgrade_tier(tier)
                if score < 8 and (nr1 == 'S' or nr2 == 'S'):
                    tier = _downgrade_tier(tier)
                if tier:
                    resolved.append((sid, target_id, tier))
                    remaining.append(f"route:{target_id}:{tier}")
        systems[sid]['notes'] = ';'.join(remaining)
    return resolved


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test():
    from .coordinates import build_canonical_id
    from .generator import generate_system
    from .names import load_register

    register = load_register('default')

    # Build a deterministic 5-system subsector
    test_ids = [
        build_canonical_id('TST', 'NET', 'A', c, r)
        for c, r in [(2, 2), (3, 4), (5, 3), (6, 6), (1, 8)]
    ]
    test_sector_id = 'NET-01'
    systems = {}
    for cid in test_ids:
        # Force presence by seeding so we can build a known layout
        s = generate_system(cid, test_sector_id, density='cluster', register=register)
        if s is None:
            # Create a minimal system manually for test coverage
            parts = parse_canonical_id(cid)
            s = {
                'id': cid, 'profile': '2M2A30', 'name': 'Test', 'region': 'TST',
                'sector': test_sector_id, 'subsector': 'A',
                'col': f"{parts['col']:02d}", 'row': f"{parts['row']:02d}",
                'ni': '', 'nr': '', 'notes': '',
                '_ac': 2, '_hz': 2, '_rx': 'M', '_pp': 2, '_pw': 'A',
                '_tn': 3, '_dx': '-', '_col': parts['col'], '_row': parts['row'],
            }
        systems[cid] = s

    systems, routes = run_network_pass(systems)

    for sid, s in systems.items():
        ni = s.get('ni', '')
        nr = s.get('nr', '')
        assert ni != '', f"Ni not set for {sid}"
        assert nr != '', f"Nr not set for {sid}"
        assert nr in set('IFBSTHK'), f"Invalid Nr {nr!r} for {sid}"
        assert s['profile'] != '', f"Empty profile for {sid}"

    print(f"network: all tests passed ({len(systems)} systems, {len(routes)} routes)")
