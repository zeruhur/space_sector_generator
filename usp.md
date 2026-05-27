## The Universal System Profile (USP)

```
[Ac][Hz][Rx][Pp][Pw][Tn][Dx] - [Ni][Nr]
```

Six encounter-relevant fields, then a dash, then two network fields. The dash is load-bearing: it signals that the second block is relational, not intrinsic to the system.

---

### Field definitions

**Ac - Access** (ordinal 0-5)
How difficult is it to arrive, establish presence, and leave?
Combines physical approach, infrastructure quality, and political entry requirements into a single play-relevant fact.

| 0 | Open, well-serviced, no complications |
|---|---|
| 1 | Standard, minor friction |
| 2 | Moderate - permits, hazardous approach, poor facilities |
| 3 | Difficult - active restrictions, dangerous transit, minimal support |
| 4 | Very difficult - hostile entry, survival-level approach hazards |
| 5 | Effectively inaccessible |

---

**Hz - Hazard** (ordinal 0-5)
Environmental and physical danger to characters present in the system.

| 0 | Benign |
|---|---|
| 1 | Minor (standard precautions sufficient) |
| 2 | Moderate (specialized gear required) |
| 3 | Severe (life-threatening without significant protection) |
| 4 | Extreme (survival measured in hours unprotected) |
| 5 | Lethal (minutes) |

Hazard type - radiation, hostile biosphere, gravitational, atmospheric - is not encoded here. It surfaces in **Dx**.

---

**Rx - Resource** (typological, single letter)
What is this system worth having for? Dominant type only.

| N | Nothing / subsistence |
|---|---|
| T | Trade goods, manufactured products |
| I | Industrial capacity, production |
| M | Raw materials, extraction |
| B | Biological, agricultural, organic |
| S | Strategic, military, political leverage |
| C | Cultural: knowledge, information, pilgrimage, art |
| X | Exotic: unique, resists categorization |

---

### Pp - Population (ordinal 0-5)

The question this field answers is not "how many people live here" but "what is the experiential density of this system?" That keeps it encounter-first rather than simulation-first.

| 0 | Empty - no permanent inhabitants |
|---|---|
| 1 | Outpost - dozens to hundreds; everyone knows everyone |
| 2 | Sparse - thousands; frontier texture, visible limits of infrastructure |
| 3 | Settled - tens of thousands to low millions; functioning society, anonymous enough to get lost in |
| 4 | Populated - high millions; urban centers, layered economy, institutional complexity |
| 5 | Dense - billions; deep social stratification, significant internal variation |

The gap between 0 and 1 is meaningful: a Pp0 system with high Tn and Dx=H is a ghost system - something happened here. A Pp0 with low Tn and Rx=X is a pristine anomaly. The population field doesn't need to encode why a system is empty; the surrounding fields do that work.

---

**Pw - Power** (typological, single letter)
Nature and structure of authority. Not government type - the question is: *who actually controls this system, and how coherently?*

| V | Void - uninhabited or no effective authority |
|---|---|
| A | Anarchic - contested, no dominant power |
| L | Local - self-governing, inward-facing |
| C | Corporate - commercial entity holds primary power |
| S | State - conventional bounded political authority |
| H | Hegemonic - dominant, reaches beyond the system |
| E | External - governed from elsewhere, client system |

---

**Tn - Tension** (ordinal 0-5)
Active conflict intensity, regardless of source (economic, military, ideological, factional).

| 0 | Stable |
|---|---|
| 1 | Low friction |
| 2 | Active disputes, minor incidents |
| 3 | Significant conflict, factional violence |
| 4 | Open warfare, systemic breakdown |
| 5 | Catastrophic - civilizational collapse in progress |

---

**Dx - Distinctiveness** (typological, single letter)
The oracle slot. What makes this system memorable, anomalous, or worth a second look? One dominant trait, chosen or generated. Dash if nothing remarkable.

| - | Nothing exceptional |
|---|---|
| X | Xenobiological - alien life, unusual biosphere |
| P | Physical phenomenon - astronomical or geological anomaly |
| H | Historical - ruins, significant past events, contested legacy |
| T | Technological - unusual capability, artifact, active research |
| C | Cultural - singular society, ideology, religious center |
| R | Restricted - something deliberately hidden or controlled |
| W | Weird - referee wildcard, defies categorization |

---

### Network layer

**Ni - Network Importance** (ordinal 0-5)
How significant is this system within the interstellar network? Derived during route-pass generation, not rolled independently.

| 0 | Irrelevant at network scale |
|---|---|
| 1 | Local significance only |
| 2 | Regional node |
| 3 | Meaningful sector-level presence |
| 4 | Major node, cross-sector relevance |
| 5 | Critical - loss would reshape the network |

**Nr - Network Role** (typological, single letter)
What function does this system perform in the network?

| B | Backwater - low connectivity, primarily destination |
|---|---|
| T | Transit - passage point on established routes |
| H | Hub - high connectivity, multi-route node |
| K | Chokepoint - bottleneck, strategic control point |
| F | Frontier - edge of settled or charted space |
| S | Sanctuary - refuge, neutral ground, off the main lines |
| I | Isolated - effectively disconnected |

---

## What a string looks like

```
32M2A3X - 4K
```

Access 3, Hazard 2, Raw materials, sparse population (outpost-scale), anarchic authority, active conflict (3), xenobiological anomaly. Network importance 4, chokepoint.

A mining system, dangerous to reach, no clear authority, actively contested, with alien biology complicating extraction. And it sits on a bottleneck route that powerful actors want to control. That's a complete adventure seed in nine characters.

---

### Field count summary

| Position | Code | Type | Range |
|---|---|---|---|
| 1 | Ac | Ordinal | 0-5 |
| 2 | Hz | Ordinal | 0-5 |
| 3 | Rx | Typological | N T I M B S C X |
| 4 | Pp | Ordinal | 0-5 |
| 5 | Pw | Typological | V A L C S H E |
| 6 | Tn | Ordinal | 0-5 |
| 7 | Dx | Typological | - X P H T C R W |
| - | separator | | |
| 8 | Ni | Ordinal | 0-5 |
| 9 | Nr | Typological | B T H K F S I |

Seven intrinsic fields, two relational fields. The ordinal fields use 0-5 throughout for consistency - no field requires extended hex notation, which keeps the string readable without a conversion table. The typological fields use letters that are reasonably mnemonic.

---

### What the schema can express

A few stress-test examples to verify the schema handles edge cases well:

`00N0V0- - 0I` - a genuinely empty, featureless, isolated system with no network relevance. The referee knows immediately: nothing here, don't stop.

`15B5H4R - 5K` - near-inaccessible, extreme hazard, rich biosphere, billions of inhabitants, hegemonic authority, open warfare, something deliberately hidden. Network-critical chokepoint. This is a major setting location with multiple active story drivers.

`01T3S2- - 3T` - easy access, minimal hazard, trade-oriented, settled population, conventional state authority, low-level friction, nothing exceptional. A normal working world on a regional transit route. Exactly the texture of a standard stopover.

`40M1E5P - 1F` - very difficult to reach, benign once you're there, raw extraction economy, outpost population, externally governed, catastrophic instability, remarkable physical phenomenon. A frontier mining outpost in political freefall, governed from afar by someone who no longer controls the situation, located near something astronomically strange. The generator is already writing the adventure.

