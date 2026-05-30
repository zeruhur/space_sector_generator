import random
from .generator import ensure_raw_fields

def roll1d6(rng: random.Random) -> int:
    return rng.randint(1, 6)

def roll2d6(rng: random.Random) -> int:
    return rng.randint(1, 6) + rng.randint(1, 6)

# ---------------------------------------------------------------------------
# Step 1: Star Architecture
# ---------------------------------------------------------------------------

def _get_star_type(rng: random.Random) -> str:
    r = roll1d6(rng)
    if r <= 4: return "M (Red Dwarf)"
    if r == 5: return "K (Orange Dwarf)"
    
    # Extended table
    r2 = roll1d6(rng)
    if r2 <= 2: return "G (Yellow)"
    if r2 == 3: return "F (Yellow-White)"
    if r2 == 4: return "White Dwarf"
    if r2 == 5: return "A (White)"
    
    # Exotic table
    r3 = roll1d6(rng)
    if r3 <= 3: return "Brown Dwarf"
    if r3 == 4: return "Red Giant"
    if r3 == 5: return "Blue Giant"
    
    r4 = roll1d6(rng)
    if r4 <= 4: return "Neutron Star"
    return "Black Hole"

def _get_star_size(star_type: str, rng: random.Random) -> str:
    # Do not roll for exotic stars or White Dwarfs
    exotics = ("Brown Dwarf", "Red Giant", "Blue Giant", "Neutron Star", "Black Hole", "White Dwarf")
    if any(e in star_type for e in exotics):
        return ""
    
    r = roll1d6(rng)
    if r <= 5: return "Dwarf"
    
    r2 = roll1d6(rng)
    if r2 <= 3: return "Giant"
    if r2 <= 5: return "Supergiant"
    return "Hypergiant"

def step_1_stars(rng: random.Random) -> list:
    r = roll1d6(rng)
    if r <= 3: count = 1
    elif r <= 5: count = 2
    else:
        r2 = roll1d6(rng)
        count = 3 if r2 <= 4 else 4
    
    stars = []
    for i in range(count):
        stype = _get_star_type(rng)
        ssize = _get_star_size(stype, rng)
        name = "Primary" if i == 0 else f"Companion {i}"
        stars.append({"name": name, "type": stype, "size": ssize})
    return stars

# ---------------------------------------------------------------------------
# Step 2: Planetary Inventory
# ---------------------------------------------------------------------------

_TERRAIN_TYPES = {
    "Hostile": ["Barren", "Barren", "Hellworld", "Hellworld", "Tainted", "Ruined"],
    "Cold": ["Frozen", "Frozen", "Arctic", "Arctic", "Glacial", "Ice Shell"],
    "Dry": ["Desert", "Desert", "Arid", "Arid", "Steppe", "Tidally Locked"],
    "Temperate": ["Savanna", "Savanna", "Continental", "Continental", "Forest", "Relic"],
    "Wet": ["Tropical", "Tropical", "Archipelago", "Archipelago", "Waterworld", "Flooded"],
    "Exceptional": ["Hothouse", "Hothouse", "Garden World", "Garden World", "Ecumenopolis", "Anomalous"]
}

def _get_terrain(rng: random.Random) -> str:
    cat_roll = roll1d6(rng)
    if cat_roll <= 2: cat = "Hostile"
    elif cat_roll == 3: cat = "Cold"
    elif cat_roll == 4: cat = "Dry"
    elif cat_roll == 5: cat = "Temperate"
    else:
        r2 = roll1d6(rng)
        cat = "Wet" if r2 <= 3 else "Exceptional"
    
    type_roll = roll1d6(rng)
    terrain = _TERRAIN_TYPES[cat][type_roll-1]
    return terrain

def step_2_planets(rng: random.Random) -> list:
    count = roll1d6(rng) + 4
    planets = []
    
    hz_roll = roll1d6(rng)
    if hz_roll <= 4: hz_count = 1
    elif hz_roll == 5: hz_count = 2
    else: hz_count = 3
    
    for i in range(count):
        r = roll1d6(rng)
        if r == 1: ptype = "Gas Giant"
        elif r <= 3: ptype = "Ice Giant"
        elif r <= 5: ptype = "Terrestrial"
        else:
            r2 = roll1d6(rng)
            ptype = "Dwarf Planet" if r2 <= 3 else "Asteroid Belt"
        
        in_hz = i < hz_count
        terrain = _get_terrain(rng) if ptype == "Terrestrial" else ""
        planets.append({"type": ptype, "hz": in_hz, "terrain": terrain})
    return planets

# ---------------------------------------------------------------------------
# Step 3: Moon Inventory
# ---------------------------------------------------------------------------

def step_3_moons(planets: list, rng: random.Random) -> None:
    for p in planets:
        ptype = p["type"]
        if ptype == "Gas Giant":
            count = roll2d6(rng)
        elif ptype == "Ice Giant":
            count = roll1d6(rng) + 1
        elif ptype == "Terrestrial":
            r = roll1d6(rng)
            if r <= 3: count = 0
            elif r <= 5: count = 1
            else: count = 2
        elif ptype == "Dwarf Planet":
            count = 1 if roll1d6(rng) == 6 else 0
        else:
            count = 0
            
        moons = []
        for _ in range(count):
            r = roll1d6(rng)
            if r <= 3: mtype = "Small Rock"
            elif r <= 5: mtype = "Big Rock"
            else:
                r2 = roll1d6(rng)
                if r2 <= 4: mtype = "Planetary-mass"
                else: mtype = "Ring system"
            
            mterrain = _get_terrain(rng) if mtype == "Planetary-mass" else ""
            moons.append({"type": mtype, "terrain": mterrain})
        p["moons"] = moons

# ---------------------------------------------------------------------------
# Step 4: Space Habitats
# ---------------------------------------------------------------------------

_HABITAT_TYPES = ["O'Neill Cylinder", "O'Neill Cylinder", "Stanford Torus", "Stanford Torus", "Bernal Sphere", "Exotic"]
_EXOTIC_HABITATS = ["Bishop Ring", "Bishop Ring", "Bishop Ring", "McKendree Cylinder", "McKendree Cylinder", "Dyson Sphere"]

def step_4_habitats(rng: random.Random) -> list:
    r = roll1d6(rng)
    if r <= 4: count = 0
    elif r == 5: count = 1
    else:
        r2 = roll1d6(rng)
        count = 2 if r2 <= 4 else 3
        
    habs = []
    for _ in range(count):
        htype = _HABITAT_TYPES[roll1d6(rng)-1]
        if htype == "Exotic":
            htype = _EXOTIC_HABITATS[roll1d6(rng)-1]
        habs.append(htype)
    return habs

# ---------------------------------------------------------------------------
# Step 5: Stations and Bases
# ---------------------------------------------------------------------------

_STATION_TYPES = ["Wheeled Station", "Wheeled Station", "Zero-G Station", "Zero-G Station", "Domed Installation", "Exotic"]
_EXOTIC_STATIONS = ["Underground Facility", "Underground Facility", "Underground Facility", "Void Citadel", "Void Citadel", "Void Citadel"]
_STATION_FUNCTIONS = {
    2: "Astronomical Observatory",
    3: "Research Lab", 4: "Research Lab",
    5: "Agriculture", 6: "Agriculture",
    7: "Mining Station",
    8: "Manufacturing", 9: "Manufacturing",
    10: "Military Base", 11: "Military Base",
    12: "Energy Production"
}

def step_5_stations(rng: random.Random) -> list:
    r = roll1d6(rng)
    if r <= 2: count = 1
    elif r <= 4: count = 2
    elif r == 5: count = 3
    else: count = roll1d6(rng) + 2
    
    stations = []
    for _ in range(count):
        stype = _STATION_TYPES[roll1d6(rng)-1]
        if stype == "Exotic":
            stype = _EXOTIC_STATIONS[roll1d6(rng)-1]
        func = _STATION_FUNCTIONS[roll2d6(rng)]
        stations.append({"type": stype, "func": func})
    return stations

# ---------------------------------------------------------------------------
# Step 6: Colonies
# ---------------------------------------------------------------------------

_COLONY_TYPES = ["Domed City", "Domed City", "Modular Ground Installation", "Modular Ground Installation", "Underground Base", "Exotic"]
_EXOTIC_COLONIES = ["Arcology", "Arcology", "Arcology", "Floating Citadel", "Floating Citadel", "Floating Citadel"]

def step_6_colonies(rng: random.Random) -> list:
    r = roll1d6(rng)
    if r <= 3: count = 0
    elif r <= 5: count = 1
    else:
        r2 = roll1d6(rng)
        count = 2 if r2 <= 3 else 3
        
    colonies = []
    for _ in range(count):
        ctype = _COLONY_TYPES[roll1d6(rng)-1]
        if ctype == "Exotic":
            ctype = _EXOTIC_COLONIES[roll1d6(rng)-1]
        colonies.append(ctype)
    return colonies

# ---------------------------------------------------------------------------
# Step 7: Population Layer
# ---------------------------------------------------------------------------

_POP_SCALE = {
    1: "Uninhabited", 2: "Outpost (10+)", 3: "Foothold (100+)",
    4: "Settlement (1,000+)", 5: "Town (10,000+)", 6: "City (100,000+)",
    7: "Metropolis (1,000,000+)", 8: "Major World (10,000,000+)",
    9: "Regional Center (100,000,000+)", 10: "Core World (1,000,000,000+)",
    11: "Ecumenopolis (10,000,000,000+)"
}

def step_7_pop_scale(pp: int, tn: int, has_hazard: bool, rng: random.Random) -> str:
    roll = roll1d6(rng) + pp
    if has_hazard or tn >= 4:
        roll -= 1
    roll = max(1, min(11, roll))
    return _POP_SCALE.get(roll, "Uninhabited")

# ---------------------------------------------------------------------------
# Step 8: Technology Level
# ---------------------------------------------------------------------------

_TECH_LEVELS = [
    (5, "Pre-Industrial"), (7, "Machine Age"), (9, "Atomic Age"),
    (11, "Information Age"), (13, "Space Age"), (15, "Stellar Age")
]

def step_8_tech(pp: int, rng: random.Random) -> str:
    roll = roll2d6(rng) + pp
    for threshold, level in _TECH_LEVELS:
        if roll <= threshold:
            return level
    return "Interstellar Age"

# ---------------------------------------------------------------------------
# Main Expansion Function
# ---------------------------------------------------------------------------

def expand_system(system: dict) -> str:
    """Follow the steps in system_detail_expansion.md to generate a full system record."""
    ensure_raw_fields(system)
    rng = random.Random(system['id'] + "-expansion")
    
    # Context from SEP
    hz = system['_hz']
    pp = system['_pp']
    tn = system['_tn']
    rx = system['_rx']
    dx = system['_dx']
    
    # 1. Stars
    stars = step_1_stars(rng)
    
    # 2. Planets
    planets = step_2_planets(rng)
    
    # 3. Moons
    step_3_moons(planets, rng)
    
    # 4. Habitats
    habitats = step_4_habitats(rng)
    
    # 5. Stations
    stations = step_5_stations(rng)
    
    # 6. Colonies
    colonies = step_6_colonies(rng)
    
    # 7. Population (Assign to planets/habitats/etc.)
    tech = step_8_tech(pp, rng)
    
    # Formatting the record
    lines = []
    lines.append(f"**Star Architecture**")
    for s in stars:
        lines.append(f"- {s['name']}: {s['type']} {s['size']}".strip())
    lines.append("")
    
    lines.append("**Orbital Bodies**")
    for i, p in enumerate(planets):
        hz_tag = " (Habitable Zone)" if p['hz'] else ""
        terrain_tag = f", {p['terrain']}" if p['terrain'] else ""
        lines.append(f"- Planet {i+1}: {p['type']}{hz_tag}{terrain_tag}")
        for m in p.get('moons', []):
            mterrain = f" ({m['terrain']})" if m['terrain'] else ""
            lines.append(f"  - Moon: {m['type']}{mterrain}")
    lines.append("")
    
    if habitats or stations or colonies:
        lines.append("**Artificial Structures**")
        for h in habitats:
            lines.append(f"- Habitat: {h}")
        for s in stations:
            lines.append(f"- Station: {s['type']} ({s['func']})")
        for c in colonies:
            lines.append(f"- Colony: {c}")
        lines.append("")
    
    lines.append("**Population**")
    overall_pop = step_7_pop_scale(pp, tn, hz >= 4, rng)
    lines.append(f"- Scale: {overall_pop}")
    lines.append(f"- Distribution: Concentrated in major settlements and stations.")
    lines.append("")
    
    lines.append("**Technology**")
    lines.append(f"- Level: {tech}")
    lines.append("")
    
    lines.append("**Local Conditions**")
    lines.append(f"- Access: {'Hostile patrols and restrictions' if system['_ac'] >= 3 else 'Open and well-serviced'}")
    lines.append(f"- Hazards: {'Extreme environmental threats' if hz >= 4 else 'Standard cosmic baseline'}")
    lines.append(f"- Tension: {'High conflict and instability' if tn >= 3 else 'Relatively stable'}")
    lines.append(f"- Distinctiveness: {dx if dx != '-' else 'Nothing exceptional'}")
    lines.append("")
    
    lines.append("**Referee Notes**")
    lines.append(f"- Primary resource: {rx}")
    if dx != '-':
        lines.append(f"- Unique feature: {dx} is a defining element of this system.")
    lines.append("- What matters here: Economic output and strategic position.")
    lines.append("- What is dangerous here: Local environmental hazards and factional friction.")
    
    return "\n".join(lines)
