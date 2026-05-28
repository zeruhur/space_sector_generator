# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Run the generator
python -m sector_gen generate --scope subsector --region-name "Orion" --sector-name "Cassian" --id A
python -m sector_gen build --input cas.tsv --scope subsector --region-name "Orion" --sector-name "Cassian" --id B
python -m sector_gen reroll --input cas.tsv --id ORT-CAS-A0304
python -m sector_gen render --input cas.tsv --scope subsector --id ORT-CAS-01-A --output out.svg

# Run all tests
python -m sector_gen test
```

No install step. Python 3.10+, standard library only.

## Architecture

The pipeline flows left to right, one module per concern:

```
coordinates.py  →  generator.py  →  network.py  →  names.py
                                                 →  io.py
                                                 →  renderer.py
```

`__main__.py` wires the pipeline into the CLI verbs (`generate`, `build`, `reroll`, `render`, `test`). `config.py` holds the only numeric constants (grid dimensions, density thresholds, defaults).

### Generation pipeline

1. **coordinates.py** — canonical ID parsing/building, hex distance (odd-offset cube coordinates), subsector edge detection, `derive_code()` for human-name → short-code derivation.
2. **generator.py** — steps 1–7 (Hz → Rx → Pp → Pw → Ac → Tn → Dx). Each step is a pure function taking a `random.Random` instance. `generate_system(canonical_id, …)` seeds `random.Random(canonical_id)` and runs the full pipeline deterministically. Rerolls use `canonical_id + f"-reroll{n}"` as seed.
3. **network.py** — runs after all systems in a subsector exist. Computes Ni (network importance), conn (within-2-hex neighbor count), articulation points (iterative Tarjan), Nr (network role), intra-subsector routes (Ni-pair scoring), and cross-subsector pending links written to `notes`.
4. **names.py** — syllable-based name generation from phoneme register JSON files in `sector_gen/phonemes/`. Seed is `canonical_id + "-name"`, keeping name generation independent from field generation.
5. **io.py** — `load_tsv` / `save_tsv` / `merge` / `get_pending_links`. `merge` is additive: existing entries always win.
6. **renderer.py** — pure SVG string construction (no external deps). Flat-top hex geometry. `render_subsector` → `render_sector` → `render_region` compose by embedding inner SVGs as `<g>` groups.

### System dict internals

`generate_system()` returns a dict with TSV fields (`id`, `profile`, `name`, `region`, `sector`, `subsector`, `col`, `row`, `ni`, `nr`, `notes`) plus ephemeral `_`-prefixed raw fields (`_ac`, `_hz`, `_rx`, `_pp`, `_pw`, `_tn`, `_dx`, `_col`, `_row`). The `_` fields are never written to TSV; `ensure_raw_fields()` re-derives them from the profile string when loading from disk.

### Canonical ID format

```
REGION-SECTOR-LXXYY   e.g. ORT-CAS-C0304
```
- REGION: 2–4 uppercase letters
- SECTOR: 2–4 uppercase letters (no sector number in the ID itself)
- L: subsector letter A–P (4×4 grid, reading order)
- XX: hex column 01–08, YY: hex row 01–10

A sector is 32×40 hexes (4 subsectors wide × 4 tall, each 8×10).

### CLI name derivation

The CLI takes `--region-name` and `--sector-name` as human-readable names and derives short codes using `derive_code()` (first N characters of stripped/uppercased name, extended if there's a collision). The internal code (e.g. `ORT`, `CAS`) is not passed directly on the command line.

### Profile format

7-char base: `AcHzRxPpPwTnDx` (e.g. `32M2A3X`). After network pass: `AcHzRxPpPwTnDx-NiNr` (10 chars, e.g. `32M2A3X-4K`). `parse_profile()` in `generator.py` handles both forms. In SVG display only, Dx=`-` is rendered as `.` to avoid visual confusion with the separator dash.

### Cross-subsector links

When a system is near a subsector edge, `detect_pending_links()` writes `pending-link:TARGET_ID` tags into the system's `notes` field. `resolve_pending_links()` scores and converts them to `route:TARGET_ID:Tier` when both endpoints exist in the loaded systems dict.
