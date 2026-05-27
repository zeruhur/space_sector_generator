# sector_gen

Procedural interstellar sector generator for tabletop RPGs.

Generates star systems with full encounter profiles (SEP), intra-subsector network ratings, and trade-route classification. Output is TSV. No external dependencies.

---

## Installation

No installation required. Clone or copy the repo and run directly.

**Requirements:** Python 3.10+, standard library only.

---

## Usage

### generate

Create a new sector, subsector, or system from scratch.

```
python -m sector_gen generate --scope <region|sector|subsector|system> [options]
```

**Examples:**

```bash
# Generate a single subsector (stdout)
python -m sector_gen generate --scope subsector --id ORT-CAS-01-A

# Generate a full sector to a file, with liquid-register names
python -m sector_gen generate --scope sector --id ORT-CAS-01 --phonemes liquid --output cas.tsv

# Generate a 6-sector region
python -m sector_gen generate --scope region --sectors 6 --region ORT --output ort_region.tsv

# Generate one system
python -m sector_gen generate --scope system --id ORT-CAS-C0304
```

**Options:**

| Flag | Default | Description |
|------|---------|-------------|
| `--scope` | (required) | `region`, `sector`, `subsector`, or `system` |
| `--id` | (required for sector/subsector/system) | Canonical ID at the target scope |
| `--region` | `GEN` | 2–4-letter region code when scope is sector or subsector |
| `--sectors N` | 4 | Number of sectors (region scope only) |
| `--density` | `standard` | `sparse`, `standard`, `dense`, or `cluster` |
| `--phonemes` | `default` | Phoneme register for name generation |
| `--output FILE` | stdout | TSV output path |

---

### build

Extend an existing TSV with new systems. Existing entries are preserved exactly.

```
python -m sector_gen build --input FILE --scope <sector|subsector|system> --id ID [options]
```

**Examples:**

```bash
# Add subsector B adjacent to an existing subsector A file
python -m sector_gen build --input cas.tsv --scope subsector --id ORT-CAS-01-B

# Add a single system to an existing file
python -m sector_gen build --input cas.tsv --scope system --id ORT-CAS-C0304 --output cas_updated.tsv
```

Cross-subsector pending links are resolved automatically when both sides are present.

---

### reroll

Replace a single system with a new randomly generated one.

```
python -m sector_gen reroll --input FILE --id SYSTEM_ID [--reroll-index N]
```

**Examples:**

```bash
python -m sector_gen reroll --input cas.tsv --id ORT-CAS-A0304
python -m sector_gen reroll --input cas.tsv --id ORT-CAS-A0304 --reroll-index 2
```

Each reroll index produces a distinct, deterministic result. The network pass is re-run for the affected subsector after the reroll.

---

### render

Render systems to an SVG file.

```
python -m sector_gen render --input FILE --scope <subsector|sector> --id ID --output FILE.svg
```

**Examples:**

```bash
python -m sector_gen render --input cas.tsv --scope subsector --id ORT-CAS-01-A --output subsector_a.svg
python -m sector_gen render --input cas.tsv --scope sector --id ORT-CAS-01 --output cas_sector.svg --color
```

**Options:**

| Flag | Description |
|------|-------------|
| `--show-profile` | Print the SEP profile string inside each hex |
| `--color` | Color mode: Hz as fill tint, primary routes in blue |

---

### test

Run the built-in test suite.

```
python -m sector_gen test
```

---

## ID format

```
[RegionCode]-[SectorName]-[SubsectorLetter][Col][Row]
```

- **RegionCode**: 2–4 uppercase letters, e.g. `ORT`
- **SectorName**: 2–4 uppercase letters, e.g. `CAS`
- **SubsectorLetter**: `A`–`P` (4×4 grid within sector, reading order)
- **Col**: `01`–`08` (hex column within subsector)
- **Row**: `01`–`10` (hex row within subsector)

Full example: `ORT-CAS-C0304`

A sector is a 32×40 hex grid divided into 16 subsectors (4 wide × 4 tall). Each subsector is 8 columns × 10 rows.

---

## TSV output format

One line per system, tab-separated, with a header row.

| Column | Description |
|--------|-------------|
| `id` | Full canonical identifier |
| `profile` | System Encounter Profile string: `AcHzRxPpPwTnDx-NiNr` |
| `name` | Generated system name |
| `region` | Region code |
| `sector` | Sector ID (e.g. `CAS-01`) |
| `subsector` | Subsector letter |
| `col` | Hex column (zero-padded) |
| `row` | Hex row (zero-padded) |
| `ni` | Network Importance digit (0–5), blank before network pass |
| `nr` | Network Role letter, blank before network pass |
| `notes` | Referee annotations; also used for pending/resolved route links |

**Profile field:** The 7-character base `AcHzRxPpPwTnDx` is present immediately after generation. After the network pass it becomes `AcHzRxPpPwTnDx-NiNr` (10 characters including the separator dash).

---

## Phoneme registers

Four built-in registers ship with the tool:

| Register | Character | Best for |
|----------|-----------|----------|
| `default` | Balanced, consonant-leaning | General use |
| `angular` | Hard stops, clipped vowels | Militaristic, industrial |
| `liquid` | Vowel-heavy, flowing | Ancient, organic |
| `eastern` | Rhythmic, alternating CV | Ceremonial, ordered |

### Writing your own phoneme file

Place a `.json` file in `sector_gen/phonemes/`. Specify it by stem name with `--phonemes`.

```json
{
  "name": "myregister",
  "description": "One-line description",
  "initial_consonants": ["k", "dr", "str"],
  "medial_consonants": ["l", "r", "n"],
  "final_consonants": ["n", "r", "k", ""],
  "vowels": ["a", "e", "i", "ou", "ae"],
  "patterns": ["CVC", "CVVC", "CCV"],
  "syllable_count": [1, 2, 2, 3],
  "joining_vowels": ["a", "e", ""]
}
```

**Pattern key:** `C` = consonant, `V` = vowel.

- First `C` in a pattern draws from `initial_consonants`
- `C` between two vowels draws from `medial_consonants`
- `C` after the last vowel draws from `final_consonants` (use `""` for open syllables)

`syllable_count` is a weighted list; each value is equally likely to be chosen.
`joining_vowels` is inserted between syllables in multi-syllable names; include `""` for no-joiner (consonant clusters at syllable boundaries).

---

## License

Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)
