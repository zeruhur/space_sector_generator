# 🚀 User Guide: Space Sector Generator

Welcome to the **Space Sector Generator**, a professional-grade worldbuilding tool designed for Game Masters and Sci-Fi writers. This guide will help you master the generation of procedural star systems and trade networks.

---

## 🛠️ Getting Started

### Requirements
- **Python 3.10** or higher.
- Standard Library only (no `pip install` required).

### Installation
Clone or download this repository. All core logic resides in the `sector_gen/` package.

---

## 🌐 Using the Web GUI (Recommended)

The Web GUI provides the most intuitive and interactive way to build your universe.

### Launching the GUI
Run the following command in your terminal:
```bash
python -m sector_gen gui
```
Open your browser and navigate to `http://localhost:8000`.

### The Workspace Concept
The GUI operates in **Workspace Mode**:
1. **Persistence:** All generated systems are automatically saved to a file called `workspace.tsv` in your project folder.
2. **Additive Generation:** Clicking "Generate Subsector" does **not** delete your previous work. It merges the new subsector into your existing workspace.
3. **Restoration:** If you close the GUI and restart it later, it will automatically reload your `workspace.tsv`.

### Interactivity
- **Zoom & Pan:** Use the **mouse wheel** to zoom and **click-and-drag** to pan across the sector map.
- **Click for Details:** Click any system (dot or name) on the map to display its **System Detail Sheet** below the viewer.
- **Natural Language:** The generator automatically translates cryptic profile codes (like `32M2A3X`) into readable paragraphs for your campaign.

### Exporting your Work
The sidebar provides five export options:
- **MD:** A professional Markdown report with a system index and detailed sheets.
- **JSON:** Machine-readable data for integration with other tools.
- **TSV:** The raw "source code" of your sector.
- **SVG:** Scalable vector map for high-quality printing.
- **PNG:** High-resolution raster image (3x scale) for quick sharing.

---

## 💻 Using the CLI (Command Line)

For advanced users and automation, the CLI offers granular control.

### Core Commands

| Command | Purpose |
|:---|:---|
| `generate` | Create a new sector, subsector, or single system from scratch. |
| `build` | Additively extend an existing TSV file. |
| `reroll` | Replace a single system with a new deterministic result. |
| `view` | Translate profiles or files into human-readable sheets in the terminal. |
| `export` | Convert TSV data to Markdown or JSON. |
| `gui` | Launch the web interface. |

### Example CLI Workflow
1. **Generate a Subsector:**
   `python -m sector_gen generate --scope subsector --region-name "Orion" --sector-name "Cassian" --id A --output my_sector.tsv`
2. **Add an Adjacent Subsector:**
   `python -m sector_gen build --input my_sector.tsv --scope subsector --region-name "Orion" --sector-name "Cassian" --id B`
3. **View a Specific System:**
   `python -m sector_gen view --input my_sector.tsv --id ORI-CAS-A0104`

---

## 🪐 Advanced Topics

### Cross-Subsector Routes
The generator handles routes that cross subsector boundaries. 
- If a system is near an edge, it creates a **`pending-link`**.
- When you generate the adjacent subsector (using the GUI or the `build` command), these links are automatically resolved into active routes if systems exist on both sides.

### Phoneme Registers
You can change the "vibe" of system names using registers:
- `default`: Balanced names.
- `angular`: Industrial/Militaristic.
- `liquid`: Ancient/Organic.
- `eastern`: Rhythmic/Ordered.

**GUI Usage:** Currently uses `default`.
**CLI Usage:** Add `--phonemes liquid` to your generate command.

### Determinism
The generator is **deterministic**. The same ID (e.g., `ORI-CAS-A0101`) will always produce the same system and name, provided you use the same version of the code. This ensures your universe remains stable.

---

## 📝 GM Tips
- **Network Importance (Ni):** Focus your high-level politics on systems with Ni 4 or 5. These are the hubs that hold the sector together.
- **Tension (Tn):** Systems with Tn 4 or 5 are in active conflict. They are perfect starting locations for adventure.
- **Distinctiveness (Dx):** Use this field as your primary "Oracle" to decide what makes a system special.

---

*Created by [zeruhur](https://github.com/zeruhur). Licensed under the MIT License.*
