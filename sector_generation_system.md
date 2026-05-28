# Sector Generation System

### An agnostic tool for procedural space opera worldbuilding

*Licensed under Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)*

## Design philosophy

This system generates interstellar sectors for tabletop roleplaying games. It is setting-agnostic: it assumes faster-than-light travel and inhabited systems, and nothing else. It does not model a specific physics, a specific FTL metaphysics, or a specific political context. The outputs are designed to be encounter-first - every field answers a question a referee or player would actually ask at the table, not a question a simulator would ask.

The full procedure requires only two six-sided dice and a pencil.

## The System Encounter Profile (SEP)

Every system in a sector is described by a nine-character string divided into two blocks:

```
[Ac][Hz][Rx][Pp][Pw][Tn][Dx] - [Ni][Nr]
```

The first block (seven characters) encodes intrinsic facts about the system. The second block (two characters, separated by a dash) encodes relational facts - the system's position and function within the interstellar network. The dash is load-bearing: it marks the boundary between what a system is and what it means.

### Field definitions

**Ac - Access** (ordinal 0-5)
How difficult is it to arrive, establish presence, and leave? Combines physical approach, infrastructure quality, and political entry requirements into a single play-relevant fact.

| Value | Meaning |
|---|---|
| 0 | Open, well-serviced, no complications |
| 1 | Standard, minor friction |
| 2 | Moderate - permits, hazardous approach, poor facilities |
| 3 | Difficult - active restrictions, dangerous transit, minimal support |
| 4 | Very difficult - hostile entry, survival-level approach hazards |
| 5 | Effectively inaccessible |

---

**Hz - Hazard** (ordinal 0-5)
Environmental and physical danger to characters present in the system. Hazard type - radiation, hostile biosphere, gravitational, atmospheric - is not encoded here; it surfaces in Dx.

| Value | Meaning |
|---|---|
| 0 | Benign |
| 1 | Minor (standard precautions sufficient) |
| 2 | Moderate (specialized gear required) |
| 3 | Severe (life-threatening without significant protection) |
| 4 | Extreme (survival measured in hours unprotected) |
| 5 | Lethal (minutes) |

---

**Rx - Resource** (typological, single letter)
What is this system worth having for? Dominant type only.

| Code | Meaning |
|---|---|
| N | Nothing / subsistence |
| T | Trade goods, manufactured products |
| I | Industrial capacity, production |
| M | Raw materials, extraction |
| B | Biological, agricultural, organic |
| S | Strategic, military, political leverage |
| C | Cultural: knowledge, information, pilgrimage, art |
| X | Exotic: unique, resists categorization |

---

**Pp - Population** (ordinal 0-5)
Not a headcount but an experiential density: what texture does human (or sophont) presence give to this system?

| Value | Meaning |
|---|---|
| 0 | Empty - no permanent inhabitants |
| 1 | Outpost - dozens to hundreds; everyone knows everyone |
| 2 | Sparse - thousands; frontier texture, visible limits of infrastructure |
| 3 | Settled - tens of thousands to low millions; functioning society, anonymous enough to get lost in |
| 4 | Populated - high millions; urban centers, layered economy, institutional complexity |
| 5 | Dense - billions; deep social stratification, significant internal variation |

A Pp 0 system is not automatically unremarkable. A Pp 0 with high Tn and Dx = H is a ghost system. A Pp 0 with Rx = X is a pristine anomaly. The surrounding fields explain the absence.

---

**Pw - Power** (typological, single letter)
Who controls this system, and how coherently? Not a government type but a structural fact about authority.

| Code | Meaning |
|---|---|
| V | Void - uninhabited or no effective authority |
| A | Anarchic - contested, no dominant power |
| L | Local - self-governing, inward-facing |
| C | Corporate - commercial entity holds primary power |
| S | State - conventional bounded political authority |
| H | Hegemonic - dominant, reaches beyond the system |
| E | External - governed from elsewhere, client system |

---

**Tn - Tension** (ordinal 0-5)
Active conflict intensity, regardless of source: economic, military, ideological, factional.

| Value | Meaning |
|---|---|
| 0 | Stable |
| 1 | Low friction |
| 2 | Active disputes, minor incidents |
| 3 | Significant conflict, factional violence |
| 4 | Open warfare, systemic breakdown |
| 5 | Catastrophic - civilizational collapse in progress |

---

**Dx - Distinctiveness** (typological, single letter)
The oracle slot. One dominant trait that makes this system memorable, anomalous, or worth a second look. Dash if nothing is remarkable.

| Code | Meaning |
|---|---|
| - | Nothing exceptional |
| X | Xenobiological - alien life, unusual biosphere |
| P | Physical phenomenon - astronomical or geological anomaly |
| H | Historical - ruins, significant past events, contested legacy |
| T | Technological - unusual capability, artifact, active research |
| C | Cultural - singular society, ideology, religious center |
| R | Restricted - something deliberately hidden or controlled |
| W | Weird - referee wildcard, defies categorization |

### Network fields

**Ni - Network Importance** (ordinal 0-5)
How significant is this system within the interstellar network? Derived during the network pass, not rolled independently.

| Value | Meaning |
|---|---|
| 0 | Irrelevant at network scale |
| 1 | Local significance only |
| 2 | Regional node |
| 3 | Meaningful sector-level presence |
| 4 | Major node, cross-sector relevance |
| 5 | Critical - loss would reshape the network |

---

**Nr - Network Role** (typological, single letter)
What function does this system perform in the network?

| Code | Meaning |
|---|---|
| B | Backwater - low connectivity, primarily a destination |
| T | Transit - passage point on established routes |
| H | Hub - high connectivity, multi-route node |
| K | Chokepoint - bottleneck, strategic control point |
| F | Frontier - edge of settled or charted space |
| S | Sanctuary - refuge, neutral ground, off the main lines |
| I | Isolated - effectively disconnected |

### Reading a profile string

```
32M2A3X - 4K
```

Access 3 (difficult), Hazard 2 (moderate), Raw materials, Population 2 (sparse outpost), Anarchic authority, Tension 3 (factional violence), Xenobiological anomaly. Network importance 4 (major node), Chokepoint.

A hard-to-reach extraction site with no stable authority, actively contested, complicated by alien biology - sitting on a critical bottleneck route. Nine characters. Complete adventure seed.

```
00N0V0- - 0I
```

Empty, benign, nothing here, isolated. Don't stop.

```
15B5H4R - 5K
```

Near-inaccessible, extreme hazard, rich biosphere, billions of inhabitants, hegemonic authority, open warfare, something deliberately hidden. Network-critical chokepoint. A major setting location with every story driver running simultaneously.

```
01T3S2- - 3T
```

Easy access, minimal hazard, trade economy, settled population, conventional state, low friction, nothing exceptional. A normal working world on a regional route. The texture of a standard stopover.

## Sector and subsector cataloging

### Hierarchy

| Level | Structure | Label |
|---|---|---|
| Region | grouping of sectors | thematic name |
| Sector | 32 x 40 hexes (4 x 4 subsectors) | name + code (e.g. CAS-01) |
| Subsector | 8 x 10 hexes | letter A through P within sector |
| System | individual hex | 4-digit coordinate XXYY within subsector |

### Canonical identifier format

Every system in the universe has a single stable identifier:

```
[RegionCode]-[SectorCode]-[SubsectorLetter][HexXX][HexYY]
```

Example: `ORT-CAS-C0304` - Outer Rim region, Cassian Sector, subsector C, hex column 03 row 04.

This identifier is the primary key for all data about that system. Names, annotations, and extended detail are layered on top of it but the identifier never changes.

### Assigning RegionCode and SectorCode

**RegionCode** is derived from the region's proper name by taking its first three letters, uppercased. If that code already exists in the universe, a fourth letter is appended to disambiguate. The referee confirms uniqueness against all existing codes before generating.

```
Outer Reach   →  OUT
Cassian Belt  →  CAS
Vordun Arc    →  VOR
```

**SectorCode** is derived from the sector's proper name by the same rule - first three letters uppercased - plus a sequential two-digit index representing the order in which the sector was created within its region. The index starts at 01 and increments with each new sector added to that region. It is a creation-order index, not a spatial coordinate.

```
Cassian Sector, first created in its region    →  CAS-01
Cassian Expanse, second created, name collides →  CASe-02
```

Spatial relationships between sectors are expressed on the map, not in the code. The code exists only to be unique and stable.

**SubsectorLetter** is assigned by position within the sector: A through P in reading order, left to right, top to bottom. A is the top-left subsector, P is the bottom-right. This is fixed by the grid and requires no decision.

## Generation procedure

### Tools required

Two six-sided dice (2d6) and one six-sided die (1d6). The entire procedure uses only these.

When a step calls for 2d6, roll both and add them. When it calls for 1d6, roll one.

### Step 0 - System presence

Assign a density class to the sector before rolling any hexes. This is a setting decision made once per sector, not generated.

| Density class | System present on |
|---|---|
| Sparse | 1d6 result of 5+ |
| Standard | 1d6 result of 4+ |
| Dense | 1d6 result of 3+ |
| Cluster | 1d6 result of 2+ |

Roll 1d6 for each hex. Mark present systems on your map. For every hex with a system, proceed through Steps 1 through 8 in order.

### Step 1 - Hz (Hazard)

Roll 2d6. No modifiers.

| 2d6 | Hz |
|---|---|
| 2 | 5 |
| 3-4 | 4 |
| 5-6 | 3 |
| 7-9 | 2 |
| 10-11 | 1 |
| 12 | 0 |

### Step 2 - Rx (Resource)

Roll 2d6.

| 2d6 | Rx |
|---|---|
| 2 | N |
| 3 | B |
| 4-5 | T |
| 6-8 | M |
| 9 | I |
| 10 | C |
| 11 | S |
| 12 | X |

**Modifier:** if Hz is 4 or 5, any result of T, I, or B becomes M instead. Hostile environments cannot sustain trade, manufacturing, or agriculture at scale - only extraction.

### Step 3 - Pp (Population)

Roll 2d6, then subtract Hz from the result.

| Modified total | Pp |
|---|---|
| 3 or less | 0 |
| 4-5 | 1 |
| 6-7 | 2 |
| 8-9 | 3 |
| 10-11 | 4 |
| 12 or more | 5 |

**Hard caps:** if Hz is 5, Pp cannot exceed 1. If Hz is 4, Pp cannot exceed 2. Apply these after the table.

### Step 4 - Pw (Power)

Pw is not rolled freely. Pp constrains the available outcomes.

**If Pp = 0:** Pw = V automatically. Skip the roll.

**If Pp = 1:** Roll 1d6.

| 1d6 | Pw |
|---|---|
| 1-2 | V |
| 3-4 | A |
| 5-6 | E |

**If Pp = 2:** Roll 1d6.

| 1d6 | Pw |
|---|---|
| 1 | A |
| 2-3 | L |
| 4 | C |
| 5 | E |
| 6 | A |

**If Pp = 3:** Roll 1d6.

| 1d6 | Pw |
|---|---|
| 1 | A |
| 2-3 | L |
| 4 | C |
| 5 | S |
| 6 | E |

**If Pp = 4:** Roll 1d6.

| 1d6 | Pw |
|---|---|
| 1 | L |
| 2-3 | C |
| 4-5 | S |
| 6 | H |

**If Pp = 5:** Roll 1d6.

| 1d6 | Pw |
|---|---|
| 1 | C |
| 2-3 | S |
| 4-5 | H |
| 6 | E |

### Step 5 - Ac (Access)

Roll 2d6. Apply all applicable modifiers, then consult the table.

**Modifiers to the roll:**

| Condition | Modifier |
|---|---|
| Hz 1-2 | -1 |
| Hz 3-4 | -2 |
| Hz 5 | -3 |
| Pw = V | -2 |
| Pw = A | -1 |
| Pw = C | +1 |
| Pw = E | +1 |
| Pw = H | +2 |

| Modified total | Ac |
|---|---|
| 12 or more | 0 |
| 10-11 | 1 |
| 8-9 | 2 |
| 6-7 | 3 |
| 4-5 | 4 |
| 3 or less | 5 |

### Step 6 - Tn (Tension)

Roll 2d6. Apply all applicable modifiers, then consult the table.

**Modifiers to the roll:**

| Condition | Modifier |
|---|---|
| Pp 0 | -3 |
| Pp 1-2 | -1 |
| Pp 4 | +1 |
| Pp 5 | +2 |
| Pw = V | -2 |
| Pw = A | +2 |
| Pw = H | +1 |
| Rx = S | +1 |

| Modified total | Tn |
|---|---|
| 3 or less | 0 |
| 4-5 | 1 |
| 6-7 | 2 |
| 8-9 | 3 |
| 10-11 | 4 |
| 12 or more | 5 |

### Step 7 - Dx (Distinctiveness)

Roll 1d6. On a 1 or 2, Dx = dash (nothing exceptional). On 3-6, roll 1d6 again on the sub-table.

**Exception:** if Hz is 4 or 5, reroll a dash result once. Extreme environments are always notable.

| Second 1d6 | Dx |
|---|---|
| 1 | X |
| 2 | P |
| 3 | H |
| 4 | Roll 1d6: 1-3 = T, 4-6 = C |
| 5 | R |
| 6 | W |

**Special case:** if Rx = X (exotic resource), Dx is automatically determined by rolling 1d6: 1-2 = P, 3-4 = X, 5-6 = H. The exotic resource and the anomaly are the same thing.

### Step 8 - Network pass (Ni and Nr)

This step runs once per subsector after all systems have been generated through Step 7. It requires the full picture before it can resolve.

**Ni - Importance**

For each system, calculate a raw score:

```
raw score = Pp + (5 - Ac)
```

Then add the following where applicable:

| Condition | Addition |
|---|---|
| Rx = S or T | +2 |
| Pw = H | +2 |
| Tn = 4 or 5 | +1 |

Look up the final raw score:

| Raw score | Ni |
|---|---|
| 0-2 | 0 |
| 3-5 | 1 |
| 6-8 | 2 |
| 9-10 | 3 |
| 11-12 | 4 |
| 13 or more | 5 |

**Nr - Network Role**

Count the number of other systems within 2 hexes of this system on the map. Call this the connection count. Then apply the conditions below in order, stopping at the first match.

| Condition | Nr |
|---|---|
| Connection count = 0 | I |
| Connection count = 1, hex is at subsector edge | F |
| Connection count = 1, hex is interior | B |
| Ac >= 3, Tn <= 1, Pw = L or A | S |
| Connection count 2-3 and Ni <= 2 | T |
| Connection count 2-3 and Ni >= 3 | H |
| Connection count 4 or more | H |

Check one final condition across the whole subsector after assigning all other Nr values: any system whose removal would split the subsector's connected systems into two or more disconnected groups is K, regardless of its previously assigned Nr. Check this last.

## Route determination

This procedure runs once per subsector, after the network pass is complete. You need the subsector map with all systems marked and each system's Ni and Nr noted.

### Step 1 - Establish reach

Every system has a standard reach of 2 hexes. Any system with Ni = 5 has extended reach of 3 hexes. Mark extended-reach systems on your map before proceeding.

### Step 2 - List candidate links

Working systematically across the map, list every pair of systems that fall within each other's reach. Record each pair once only. Systems with Nr = I are excluded entirely and form no links.

### Step 3 - Link activation

For each candidate pair, calculate a link score:

```
link score = Ni(A) + Ni(B) - distance penalty
```

| Distance | Penalty |
|---|---|
| 1 hex | 0 |
| 2 hexes | 2 |
| 3 hexes (extended reach only) | 4 |

A link is active if the link score is 3 or higher. Strike inactive pairs from your list.

### Step 4 - Route classification

| Link score | Tier |
|---|---|
| 3-4 | Tertiary |
| 5-7 | Secondary |
| 8 or more | Primary |

### Step 5 - Special conditions

Apply these two passes after classifying all active links.

**Nr = K (chokepoint):** Any active link where one endpoint is K is upgraded one tier. Tertiary becomes Secondary. Secondary becomes Primary. Primary stays Primary.

**Nr = S (sanctuary):** Any active link where one endpoint is S is downgraded one tier, unless the link score is 8 or higher. Secondary becomes Tertiary. Tertiary is deactivated. Sanctuaries resist becoming transit points.

### Step 6 - Cross-subsector links

For each system within reach of the subsector edge, note which edge hexes it reaches into the adjacent subsector. Record these as pending links. They are resolved when the adjacent subsector is generated, using the same procedure. The link score determines the outcome; neither contributor decides unilaterally.

## Output format

Each system produces a profile string and a canonical identifier, recorded on one line:

```
ORT-CAS-C0304   32M2A3X-4K
```

One line per system. Names, annotations, and extended detail are written separately, keyed to the identifier. The profile string and identifier together are the canonical record; everything else is commentary.

Draw routes on the map using three distinct line styles - one per tier. The network emerges from the data. No further decisions are required unless you choose to place an override by hand, which is always permitted.

---

(c) 2026 Roberto Bisceglie

*This work is released under CC BY-SA 4.0. You are free to share and adapt this material for any purpose, including commercial use, provided you give appropriate credit and distribute any adaptations under the same license.*
