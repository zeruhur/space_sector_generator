## Step 1: The Profile String

see /usp.md

---

## Step 2: Sector and Subsector Cataloging

Keep the 8x10 hex grid for the subsector. It's genuinely optimal: navigable visually, compact enough to print, granular enough to hold meaningful variation. The Traveller sector (16 subsectors, 4x4 arrangement) is also worth keeping as the structural unit above it.

Where you can differentiate is in the **naming and hierarchy above the sector level**. Traveller has sectors, then domains, then the Imperium. You can define:

- **Hex** (individual system): 4-digit coordinate XXYY within subsector
- **Subsector** (8x10): labeled A-P within a sector, with a proper name
- **Sector** (32x40): the primary cataloging unit, with a name and a canonical ID code (2-3 letters + number, e.g. RIM-01)
- **Region** (optional grouping of sectors): your equivalent of a domain, named thematically

The critical infrastructure decision is your **canonical identifier format**. Every world in your universe needs a unique, stable ID. A good format:

```
[RegionCode]-[SectorCode]-[SubsectorLetter][HexXX][HexYY]
```

Example: `ORT-CAS-C0304` means Outer Rim region, Cassian Sector, subsector C, hex 03-04. This is human-readable, sortable, and unambiguous. Establish this before generating anything, because it becomes the foreign key across all your data.

---

## Step 3: System Distribution Algorithm

The two separate concerns here are **presence** (is there a system in this hex?) and **profile** (what kind of system?). Keep them as distinct passes.

For presence, Traveller's 2D6 roll with a threshold is elegant but produces uniform density. A more interesting approach uses **stellar density zones**: each sector has a density class (sparse / standard / dense / cluster), which modifies the base presence probability. This lets you model galactic structure - core sectors dense, rim sectors sparse - without hand-placing every system.

For reproducibility across contributors (essential if you want a shared universe), use **seeded deterministic generation**. Every hex gets a seed derived from its canonical ID: `seed = hash(sector_id + subsector_letter + hex_coords)`. Any generation tool using the same algorithm and seed produces identical output. Contributors can add hand-crafted worlds by simply overriding the generated data for specific hex IDs.

The profile generation algorithm should be a table-driven process with **interdependencies baked in**. The key interdependencies in Traveller are Size → Atmosphere → Hydrosphere → Population → Government → Law → Tech. You want something similar where physical parameters constrain social ones. Define this dependency graph explicitly before writing any code; it's the hardest part to retrofit.

---

## Step 4: Route Determination

Routes in Traveller are implicitly jump-range-based, which means they're an artifact of the drive technology. Your equivalent depends on your setting's FTL metaphysics - but the mathematical approach is the same regardless.

The algorithm has two stages:

**Stage 1: Adjacency graph.** For each system, identify all systems within "reach" (whatever your FTL range unit is in hexes). This is just hex-distance calculation: `d = max(|dx|, |dy|, |dx+dy|)` in offset-coordinate hexes. Build a graph where edges connect reachable pairs.

**Stage 2: Route classification.** Weight each edge by the combined importance of its endpoints. Importance is a derived score from the profile (high population + high transit tier + high capability = high importance). Then:
- **Primary routes** are edges in the maximum spanning tree of this weighted graph - the backbone connecting the most important worlds
- **Secondary routes** are additional edges where both endpoints have above-threshold importance
- **Tertiary / local routes** are short-range connections below that threshold

This gives you a hierarchical route network that emerges from the data rather than being hand-drawn, which is exactly what you want for procedural generation at scale.

---

## Step 5: The Generation Script

The architecture I'd recommend: a **pipeline of independent passes**, each consuming and emitting structured text (JSON or TSV). This makes every stage testable in isolation and lets you swap out individual algorithms later.

```
seed_input
    → presence_pass      (hex grid + presence flags)
    → profile_pass       (generate USP for each present system)
    → extension_pass     (derive trade codes, importance scores, route weights)
    → route_pass         (build adjacency graph, classify routes)
    → output_formatter   (emit canonical text format)
```

For output, define your canonical text format before writing the script. Traveller's SEC format (sector data file) is a fixed-width columnar text file, one world per line. You want something similar: a flat format that is both human-readable and parseable without a special tool. TSV with a fixed column schema is ideal, because it opens in any spreadsheet tool and parses trivially in any language.

---

## Where to Start

The sequencing that minimizes rework:

1. Lock the profile schema (Step 1) - everything downstream depends on it
2. Lock the canonical ID format (Step 2) - this is your data spine
3. Write the dependency graph for profile generation (Step 3) - the conceptual core
4. Implement a single-subsector generator as proof of concept, output TSV
5. Add routing on top of that

The visual/map stack can wait entirely until you have stable data output for at least one sector. The data format you define now will be what map tools consume later, so getting it right matters more than getting it fast.

One question worth answering now: **are your existing RPG settings expected to be compatible at the world-generation level, or only at the setting level?** If some of your games have already published world data in any form, you'll need a migration path from that data to the canonical ID schema. If everything is still generative, you have a clean slate and can design the schema purely for elegance.