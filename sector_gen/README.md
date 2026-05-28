# sector_gen

Procedural interstellar sector generator for tabletop RPGs.

Generates star systems with full encounter profiles (SEP), intra-subsector network ratings, and trade-route classification. Output is TSV, Markdown, or JSON. Includes a modern Web GUI. No external dependencies.

---

## Installation

No installation required. Clone or copy the repo and run directly.

**Requirements:** Python 3.10+, standard library only.

---

## Usage

### gui

Start the local interactive Web GUI.

```bash
python -m sector_gen gui
```
- **Interactive Map:** Zoom and pan with the mouse.
- **Click-to-View:** Click any hex to instantly see a detailed "System Sheet" in natural language.
- **Full Reference:** Browse the built-in System Rules and User Guide.
- **One-Click Export:** Download your map as SVG/PNG or your data as TSV/JSON/Markdown.

### view

Translate system profiles to natural, GM-ready "Detail Sheets".

```bash
# Directly translate a profile string
python -m sector_gen view --profile "32M2A3X-4K"

# View sheets for all systems in a file
python -m sector_gen view --input sector.tsv

# View a specific system sheet from a file
python -m sector_gen view --input sector.tsv --id ORT-CAS-A0304
```

### export

Export generated data to professional formats for use in campaign notes (Obsidian, Foundry VTT, etc.).

```bash
# Export to a structured Markdown report with an index table and detailed sheets
python -m sector_gen export --input sector.tsv --format markdown --output report.md

# Export to a machine-readable JSON file
python -m sector_gen export --input sector.tsv --format json --output data.json
```

### generate

Create a new sector, subsector, or system from scratch.

```bash
python -m sector_gen generate --scope <region|sector|subsector|system> [options]
```

**Options:**

| Flag | Default | Description |
|------|---------|-------------|
| `--scope` | (required) | `region`, `sector`, `subsector`, or `system` |
| `--region-name` | (required) | Human-readable region name (e.g. "Orion") |
| `--sector-name` | (required*) | Human-readable sector name |
| `--density` | `standard` | `sparse`, `standard`, `dense`, or `cluster` |
| `--phonemes` | `default` | Phoneme register for name generation |
| `--output FILE` | stdout | TSV output path |

### build

Extend an existing TSV with new systems. Existing entries are preserved exactly.

```bash
python -m sector_gen build --input FILE --scope <sector|subsector|system> --id ID [options]
```

Cross-subsector pending links are resolved automatically when both sides are present.

### render

Render systems to an SVG file.

```bash
python -m sector_gen render --input FILE --scope <subsector|sector> --id ID --output FILE.svg
```

### test

Run the built-in test suite.

```bash
python -m sector_gen test
```

---

## ID format

```
[RegionCode]-[SectorName]-[SubsectorLetter][Col][Row]
```

Full example: `ORI-CAS-A0104`

A sector is a 32×40 hex grid divided into 16 subsectors (4 wide × 4 tall). Each subsector is 8 columns × 10 rows.

---

## Phoneme registers

Four built-in registers ship with the tool: `default` (balanced), `angular` (industrial), `liquid` (ancient), and `eastern` (ceremonial).

Place custom `.json` files in `sector_gen/phonemes/` to define your own linguistic patterns.

---

## License & Attribution

Created by **[zeruhur](https://github.com/zeruhur)**.

Licensed under the **MIT License**. See the `LICENSE` file for details.

Source Code: [https://github.com/zeruhur/space_sector_generator](https://github.com/zeruhur/space_sector_generator)
