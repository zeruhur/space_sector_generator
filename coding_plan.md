# Sector Generation System - Build Plan for Claude Code

## Overview

Build a command-line Python tool that procedurally generates interstellar sectors for tabletop RPGs, following a specific rules-based algorithm. The tool must run on standard library only (no external dependencies) except for an optional SVG renderer. Output is TSV. The system is designed to be agnostic, portable, and extensible by end users.

---

## Project structure

```
sector_gen/
├── __main__.py
├── config.py
├── coordinates.py
├── generator.py
├── network.py
├── names.py
├── io.py
├── renderer.py
└── phonemes/
    ├── default.json
    ├── angular.json
    ├── liquid.json
    └── eastern.json
```

No external dependencies for generation. Standard library only: `random`, `csv`, `json`, `argparse`, `pathlib`, `sys`, `copy`.

---

## CLI interface

Three verbs, one optional render step.

```
python -m sector_gen generate --scope [region|sector|subsector|system] [options]
python -m sector_gen build    --input FILE --scope [sector|subsector|system] --id ID [options]
python -m sector_gen reroll   --input FILE --id SYSTEM_ID [--reroll-index N]
python -m sector_gen render   --input FILE --scope [sector|subsector|system] --id ID --output FILE.svg
```

### generate options
- `--scope` required: region, sector, subsector, or system
- `--id` required for scope=sector/subsector/system (e.g. CAS-01, CAS-01-C, ORT-CAS-C0304)
- `--sectors N` required for scope=region (integer, contiguous layout)
- `--density [sparse|standard|dense|cluster]` default: standard
- `--phonemes REGISTER` name of phoneme file to use, default: default
- `--output FILE` TSV output path, default: stdout

### build options
- `--input FILE` existing TSV to read and extend
- `--scope` and `--id` define what scope to generate into
- Existing entries in the TSV are preserved exactly; only missing hexes are generated
- `--output FILE` default: overwrites input file (prompt for confirmation)

### reroll options
- `--input FILE` existing TSV
- `--id` canonical ID of the single system to reroll
- `--reroll-index N` integer suffix appended to seed string, default: 1, increments if user rerolls same system again
- Outputs updated TSV with that one line replaced

### render options
- `--input FILE` TSV to render
- `--scope` and `--id` define the viewport (render one subsector, one sector, etc.)
- `--output FILE` SVG output path

---

## Canonical identifier format

```
[RegionCode]-[SectorCode]-[SubsectorLetter][HexXX][HexYY]
```

- RegionCode: 2-4 uppercase letters (e.g. ORT)
- SectorCode: 2-4 uppercase letters + hyphen + 2-digit number (e.g. CAS-01)
- SubsectorLetter: A through P
- HexXX: column 01-08 (zero-padded)
- HexYY: row 01-10 (zero-padded)

Full example: `ORT-CAS-C0304`

Parsing rules:
- Split on `-` to extract Region, Sector base, Sector number, and Subsector+Hex
- Subsector letter is the first character of the final segment
- HexXX is characters 2-3 of the final segment
- HexYY is characters 4-5 of the final segment

Sector layout: 4x4 grid of subsectors labeled A-P in reading order (A=top-left, P=bottom-right). A sector is 32 columns x 40 rows of hexes total.

---

## Seeding strategy

Every system is generated with a deterministic seed derived from its canonical ID.

```python
import random
random.seed(canonical_id)          # normal generation
random.seed(canonical_id + f"-reroll{n}")  # reroll with index n
```

Seed is set once at the start of each system's generation. All field rolls for that system draw from the same seeded sequence. This guarantees that generate and build produce identical results for the same hex ID.

---

## TSV output format

One line per system. Tab-separated. Header row required.

```
id	profile	name	region	sector	subsector	col	row	ni	nr	notes
ORT-CAS-C0304	32M2A3X-4K	Kethavar	ORT	CAS-01	C	03	04		
```

Fields:
- `id`: full canonical identifier
- `profile`: the 9-character SEP string formatted as `AcHzRxPpPwTnDx-NiNr`
- `name`: generated system name (string)
- `region`, `sector`, `subsector`, `col`, `row`: parsed from ID for easy filtering
- `ni`, `nr`: repeated from profile for easy network queries
- `notes`: empty by default, free text field for referee annotations

Network fields (ni, nr) are written as blank in the TSV immediately after per-system generation. They are filled in during the network pass. This makes it clear in the file which systems have completed network resolution.

---

## Generation algorithm

Implement each step as a separate function in `generator.py`. Every function takes the current system state (a dict) and returns it updated. This makes the pipeline explicit and testable.

### Step 0 - Presence check (in coordinates.py or generator.py)

```
density thresholds (1d6 roll, system present if result >=):
  sparse:   5
  standard: 4
  dense:    3
  cluster:  2
```

### Step 1 - Hz

Roll 2d6.

```
2:      Hz = 5
3-4:    Hz = 4
5-6:    Hz = 3
7-9:    Hz = 2
10-11:  Hz = 1
12:     Hz = 0
```

### Step 2 - Rx

Roll 2d6.

```
2:    Rx = N
3:    Rx = B
4-5:  Rx = T
6-8:  Rx = M
9:    Rx = I
10:   Rx = C
11:   Rx = S
12:   Rx = X
```

Modifier: if Hz >= 4 and Rx in [T, I, B], set Rx = M.

### Step 3 - Pp

Roll 2d6, subtract Hz.

```
<= 3:  Pp = 0
4-5:   Pp = 1
6-7:   Pp = 2
8-9:   Pp = 3
10-11: Pp = 4
>= 12: Pp = 5
```

Hard caps: Hz=5 → Pp = min(Pp, 1). Hz=4 → Pp = min(Pp, 2).

### Step 4 - Pw

Pw is constrained by Pp. Implement as a dict of Pp-keyed weighted tables.

```
Pp=0: Pw = V (automatic)

Pp=1 (1d6):
  1-2: V
  3-4: A
  5-6: E

Pp=2 (1d6):
  1:   A
  2-3: L
  4:   C
  5:   E
  6:   A

Pp=3 (1d6):
  1:   A
  2-3: L
  4:   C
  5:   S
  6:   E

Pp=4 (1d6):
  1:   L
  2-3: C
  4-5: S
  6:   H

Pp=5 (1d6):
  1:   C
  2-3: S
  4-5: H
  6:   E
```

### Step 5 - Ac

Roll 2d6, apply modifiers, lookup result.

Modifiers:
```
Hz 1-2: -1
Hz 3-4: -2
Hz 5:   -3
Pw=V:   -2
Pw=A:   -1
Pw=C:   +1
Pw=E:   +1
Pw=H:   +2
```

Table (after modifiers):
```
>= 12: Ac = 0
10-11: Ac = 1
8-9:   Ac = 2
6-7:   Ac = 3
4-5:   Ac = 4
<= 3:  Ac = 5
```

### Step 6 - Tn

Roll 2d6, apply modifiers, lookup result.

Modifiers:
```
Pp=0:  -3
Pp 1-2: -1
Pp=4:  +1
Pp=5:  +2
Pw=V:  -2
Pw=A:  +2
Pw=H:  +1
Rx=S:  +1
```

Table (after modifiers):
```
<= 3:  Tn = 0
4-5:   Tn = 1
6-7:   Tn = 2
8-9:   Tn = 3
10-11: Tn = 4
>= 12: Tn = 5
```

### Step 7 - Dx

First roll 1d6:
- 1-2: Dx = "-" (dash, nothing exceptional)
- 3-6: roll second 1d6 on sub-table

Exception: if Hz >= 4 and first roll gives dash, reroll once. Only once.

Sub-table (second 1d6):
```
1: X
2: P
3: H
4: roll 1d6 → 1-3: T, 4-6: C
5: R
6: W
```

Special case: if Rx = X, Dx is determined by 1d6:
```
1-2: P
3-4: X
5-6: H
```
Skip the normal Dx rolls entirely.

---

## Network pass - implement in network.py

Run once per subsector after all systems are generated through Step 7.

### Ni calculation

For each system:

```
raw = Pp + (5 - Ac)
```

Add:
```
Rx in [S, T]: +2
Pw = H:       +2
Tn in [4, 5]: +1
```

Lookup:
```
0-2:   Ni = 0
3-5:   Ni = 1
6-8:   Ni = 2
9-10:  Ni = 3
11-12: Ni = 4
>= 13: Ni = 5
```

### Nr calculation

For each system, count how many other systems are within 2 hexes (hex distance, not Euclidean). Call this `conn`.

Apply conditions in order, stop at first match:
```
conn = 0:                                    Nr = I
conn = 1 and system is at subsector edge:    Nr = F
conn = 1 and system is interior:             Nr = B
Ac >= 3 and Tn <= 1 and Pw in [L, A]:       Nr = S
conn in [2,3] and Ni <= 2:                  Nr = T
conn in [2,3] and Ni >= 3:                  Nr = H
conn >= 4:                                   Nr = H
```

After all systems have an Nr value, do one final pass: any system whose removal disconnects the subsector graph gets Nr = K, overriding whatever was assigned.

### Hex distance

Use offset-coordinate hex distance. For an 8-wide grid with offset columns:

```python
def hex_distance(col1, row1, col2, row2):
    # convert offset to cube coordinates, then use cube distance
    def to_cube(col, row):
        x = col
        z = row - (col - (col & 1)) // 2
        y = -x - z
        return x, y, z
    x1, y1, z1 = to_cube(col1, row1)
    x2, y2, z2 = to_cube(col2, row2)
    return max(abs(x1-x2), abs(y1-y2), abs(z1-z2))
```

---

## Route determination - implement in network.py

Run once per subsector after network pass.

### Reach

Standard reach: 2 hexes. Extended reach (Ni=5): 3 hexes.

### Candidate links

All pairs of non-I systems within each other's reach. Record each pair once (A,B not B,A).

### Link score

```
score = Ni(A) + Ni(B) - distance_penalty
```

```
distance 1: penalty 0
distance 2: penalty 2
distance 3: penalty 4  (extended reach only)
```

Active if score >= 3.

### Classification

```
3-4:  Tertiary
5-7:  Secondary
>= 8: Primary
```

### Special conditions

Pass 1 - K endpoints: any active link with a K endpoint upgrades one tier.
Pass 2 - S endpoints: any active link with an S endpoint downgrades one tier, unless score >= 8. Tertiary deactivated.

### Cross-subsector links

For systems within reach of the subsector boundary, record pending links in the TSV notes field as:
```
pending-link:ORT-CAS-D0108
```

These are resolved when the adjacent subsector is generated. The build verb handles this automatically: when extending a file, it checks all pending links against the existing data and resolves any that can now be scored.

---

## Name generator - implement in names.py

Syllable-based generation driven by phoneme register JSON files.

### Phoneme file format

```json
{
  "name": "default",
  "description": "Balanced, slightly consonant-heavy",
  "initial_consonants": ["k", "v", "th", "dr", "str", "m", "r", "s", "n", "br"],
  "medial_consonants": ["l", "r", "n", "v", "th", "s"],
  "final_consonants": ["n", "r", "s", "th", "k", "x", "l"],
  "vowels": ["a", "e", "i", "o", "u", "ai", "ae", "ei", "ou"],
  "patterns": ["CVC", "CVC", "CVVC", "CCV", "CCVC", "VC"],
  "syllable_count": [1, 2, 2, 2, 3],
  "joining_vowels": ["a", "e", "i", "o"]
}
```

Pattern key: C = consonant slot, V = vowel slot. Initial C draws from `initial_consonants`, medial C (between vowels) from `medial_consonants`, final C from `final_consonants`.

`syllable_count` is a weighted list - sample from it to determine how many syllables to generate. Multi-syllable names join with a character drawn from `joining_vowels`, or no joining character (include empty string in the list if desired).

### Phoneme files to ship

Four registers:

**default.json** - balanced, works for any setting

**angular.json** - harsh, hard stops, good for militaristic or industrial cultures
```
initial: kr, vx, str, gh, dr, zt, kh, br
vowels: a, e, i, aa, ei (short, clipped)
final: k, x, n, r, th, s, kt
patterns: CVC, CCVC, CVCC weighted heavily
```

**liquid.json** - soft, vowel-heavy, good for ancient or organic cultures
```
initial: m, r, l, n, v, s, sh, wh
vowels: a, ae, ai, ei, ou, io, ua, aua (long and flowing)
final: l, n, r, m, (empty)
patterns: CVC, CVVC, CV, VC weighted toward open syllables
```

**eastern.json** - rhythmic, alternating, good for ceremonial or ordered cultures
```
initial: k, s, t, h, n, m, sh, ts
vowels: a, i, u, e, o (pure, no diphthongs)
final: (empty), n, r, shi, ko
patterns: CV, CVC, CVCV (multi-syllable as single pattern)
```

### Name generation function signature

```python
def generate_name(register: dict, seed_string: str) -> str:
    random.seed(seed_string + "-name")
    # generate and return name string
```

Seed is the system's canonical ID plus "-name" suffix, keeping name generation deterministic but separate from field generation.

---

## SVG renderer - implement in renderer.py

Produces a flat SVG file. No external dependencies. Build SVG as string concatenation or with xml.etree.ElementTree from standard library.

### Hex grid geometry

Flat-top hexagons. For a hex of size S (center to vertex):
```
width  = 2 * S
height = sqrt(3) * S
horiz_spacing = 1.5 * S
vert_spacing  = sqrt(3) * S
```

Column offset: odd columns shift down by `height / 2`.

### What to render per system

- Hex outline (thin stroke, no fill or very light fill by Ni value)
- System dot at center (filled circle, radius ~4px)
- Coordinate label (tiny, below dot)
- System name (below coordinate, slightly larger)
- Profile string (optional, toggled by flag --show-profile)
- Route lines between linked systems (line weight by tier: Primary=2px, Secondary=1px, Tertiary=0.5px dashed)

### Render scopes

- Subsector: 8x10 hex grid, single SVG
- Sector: 4x4 arrangement of subsectors, larger SVG with subsector boundary lines
- Region: arrange sectors in a grid, smaller hexes to fit

### Color scheme

Monochrome by default. Use stroke weight and fill density to encode data, not color. This ensures the output prints cleanly in black and white.

Optional `--color` flag enables:
- Hz encoded as fill saturation (low = light, high = dark red)
- Primary routes in a distinct color

---

## io.py - file handling

### Functions required

```python
def load_tsv(path: Path) -> dict:
    # returns dict keyed by canonical ID
    # value is the full row as a dict

def save_tsv(path: Path, systems: dict) -> None:
    # writes all systems sorted by id

def merge(existing: dict, new_systems: dict) -> dict:
    # existing entries win; new entries fill gaps
    # returns merged dict

def get_pending_links(systems: dict) -> list:
    # parses notes fields for pending-link entries
    # returns list of (system_id, neighbor_id) tuples
```

---

## Error handling

- Invalid canonical ID format: print clear error with expected format, exit 1
- Missing input file: print error, exit 1
- Attempting to generate a scope that partially overlaps an existing file: warn and ask for confirmation before proceeding
- Unknown phoneme register: list available registers and exit 1
- Reroll on a system ID not found in input: print error, exit 1

---

## Testing

Write a test function (no test framework required, plain `assert` statements) in each module that exercises the main logic:

- `generator.py`: generate 100 systems, verify all fields are within valid ranges
- `network.py`: build a minimal 5-system subsector, verify Ni/Nr/route assignments
- `names.py`: generate 20 names per register, verify no empty strings, reasonable length (3-20 chars)
- `coordinates.py`: verify hex_distance is symmetric and produces 0 for identical coords
- `io.py`: write a TSV, read it back, verify round-trip fidelity

Run tests with:
```
python -m sector_gen test
```

---

## Deliverables

1. All Python files as specified above
2. Four phoneme JSON files
3. A README.md covering installation (none required), usage (CLI examples), and the phoneme file format so users can write their own
4. A sample output: one fully generated subsector TSV with 40 hexes processed (not all will have systems), network pass complete, routes noted

The sample output should demonstrate the full pipeline end to end and serve as a reference for contributors building adjacent subsectors.