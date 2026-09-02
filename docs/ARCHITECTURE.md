# Phylaworld — Technical Architecture

> **A pixel art, top-down 2D multiplayer world where creatures are tamed, studied, trained — and fought with in turn-based battles.**
> This document is the single source of truth for how the project is built on Godot. It is intentionally **mod-first**: everything content-related is data, so mods (and AI assistants) can author and extend the game without touching code.

---

## 1. Design Laws

These are non-negotiable; every decision below derives from them.

1. **All content is data, never code.** The game ships as a *framework* plus a built-in **base mod**. Modders can strip every creature, move, and type and the game still boots.
2. **One canonical mod format** — a folder or `.zip` containing `manifest.json` + JSON content files + optional `assets/` (png/ogg). Authored with any text editor + an archive tool (7-zip) or the in-game packager. **No Godot editor required.**
3. **Stable full IDs** (`modid:itemid`) on every content item. Renaming an id is a new id plus a deprecated alias. This is the foundation for saves, trading, multiplayer, and cross-game creature progression.
4. **Battle behavior = a JSON effect pipeline** composed from a built-in *effect library*. Mods remix existing ingredients; they never execute code. This keeps the game safe for multiplayer and the store verifiable.
5. **Determinism.** Battles use a seeded RNG, fixed resolution order, and never store floats in serialized data. Two clients with the same seed + modset reach identical results — a hard requirement for later online play.
6. **i18n built-in.** Every name/description is a string table object `{"en": "...", "es": "...", ...}`. Localizations travel inside mods.
7. **Creature DNA is the truth.** Every individual creature is a versioned, ID-only text blob used identically by saves, trading, network sync, and future franchise games.
8. **Death is a real mechanic** (unlike Pokémon). Certain circumstances permanently remove a creature; growth stages are permanent.
9. **Bond is a mechanic, not a flavor stat.** It modifies friendly fire in battle, ride performance, and base-task output — so every one of those systems reads the same bond value from DNA.
10. **The world respects ownership rules.** Bases live only in designated zones behind permission unlocks; rides require crafted gear; nothing is placeable/modifiable anywhere arbitrarily.
11. **The environment simulates physics and chemistry.** Elemental moves interact with the overworld beyond battles — fire ignites, water flows, cold freezes, heat softens metal. These rules are data, deterministic, and shared between battle and overworld.
12. **Crafting is layered and painful.** Most craftable items require specific tools, stations, and ingredient chains. Automation through creature labor is possible at bases but gated by creature capability, stamina, and sanity.

---

## 2. Stack & Platforms

- **Engine:** Godot 4.x (current project added under 4.7), renderer `gl_compatibility`, Jolt Physics for the overworld.
- **Targets:** Windows, Linux, Android, Web.
- **Art:** pixel-art 2D; Aseprite pipeline; layered/appearance-driven sprites (see §9).
- **AI-friendliness:** content is plain JSON + schemas, so the existing `addons/godot_ai` MCP integration and CLI tools can lint, generate, and bulk-edit content.

---

## 3. Repository Layout

```
res://
├─ addons/phylaworld/            # THE FRAMEWORK — engine logic only, zero content
│  ├─ mod/                       # mod_manager, zip+fs loaders, manifest parser,
│  │                             # validator, store_client, packager, asset cache
│  ├─ data/                      # content_registry, per-kind schemas, asset_resolver,
│  │                             # i18n, global balance store
│  ├─ appearance/                # layered sprite pipeline (bodyplan + variant + slots)
│  ├─ battle/                    # battle_engine, grid_arena (zones/terrain/cover),
│  │                             # move_resolver, effect_runner, effect_library (ops),
│  │                             # damage_calc, turn_order, seeded_rng,
│  │                             # format rules (1v1 / 2v2)
│  ├─ world/                     # overworld controller, tilemap helpers, spawner,
│  │                             # taming, capture (balls + emergency release),
│  │                             # riding/mounts, towers (PC-equivalent),
│  │                             # bases + base_zones + farming + automation,
│  │                             # crafting + stations + worker slots,
│  │                             # ecosystem + physics/chemistry engine,
│  │                             # underground sub-world, npc
│  ├─ meta/                      # growth_stages, lifespan/death, research/dex,
│  │                             # creature_records, breeding, nature, bond,
│  │                             # stamina/sanity/labor state
│  ├─ save/                      # save_manager, creature_dna encode/decode, migration
│  ├─ uimod/                     # battle UI, party, dex, summary, mod manager, store
│  └─ tools/                     # EditorPlugin: schema lint, content tester,
│                                # zip packager (also usable standalone/CLI)
├─ content/base/                 # BUILT-IN BASE MOD (same JSON format as any mod)
│  ├─ manifest.json
│  ├─ balance.json
│  ├─ types.json  type_chart.json  taxonomies.json  terrain.json
│  ├─ moves.json  abilities.json  statuses.json  natures.json  variants.json
│  ├─ records.json behaviors.json items.json (incl. spheres + ball_skins)
│  ├─ ride_types.json  ride_gear.json  crafting.json  crafting_stations.json
│  ├─ growth_stages.json  base_tasks.json  base_zones.json
│  ├─ ecosystem.json  physics_rules.json  map_layers.json
│  ├─ species/                   # one file per creature (or batched)
│  ├─ arenas.json  regions.json  wild_encounters.json  underground.json
│  └─ ...
├─ mods/                         # dev-time authoring folder
├─ scenes/ scripts/ ui/ assets/  # core UI + engine scenes (not content data)
└─ project.godot
```

Rule of thumb: **anything a player can encounter belongs in `content/`, never in `addons/` or `scripts/`.**

---

## 4. Content & Mods

### 4.1 Mod package
A mod is a folder or `.zip` placed in `user://mods/`:

```
MyMod.zip
├─ manifest.json          # required
├─ content/*.json         # all content files
└─ assets/                # png/ogg referenced by content
```

- `ZipReader` reads zips at runtime on every export target. Asset files are materialized once to `user://mod_cache/<modid>/assets/...` so the engine can texture them.
- Loose folders are supported for development (same structure, no zip).

### 4.2 manifest.json
```json
{
  "id": "my_mod",
  "name": {"en": "My Mod"},
  "version": "1.0.0",
  "author": "asdf",
  "description": {"en": "Adds ..."},
  "dependencies": ["base"],
  "conflicts": ["rival_mod"],
  "content": [
    "content/types.json",
    "content/creatures/emberling.json"
  ]
}
```

### 4.3 Loading pipeline
1. **ModManager** scans `user://mods/`, reads every manifest, checks dependencies/conflicts, tracks enable/disable (persisted to a settings file).
2. **ContentRegistry** parses validated files and indexes content by *kind* and *full id*.
3. Duplicate full id across active mods = a conflict surfaced in the mod-manager UI (the user picks an override order).
4. Toggling a mod applies on restart (safe default; pure-data hot-apply may come later).

### 4.4 Validation & authoring
- Every content kind has a **JSON schema**; bad content fails with a friendly error pointing at the path and field.
- The **tools layer** ships: schema linter, in-game content tester, and a **zip packager** that runs from the editor *or* a standalone CLI — so a modder never needs the Godot editor to build a distributable mod.

### 4.5 Mod store
The store is the ModManager plus HTTP: the game fetches an `index.json` from a server, lists mods, downloads `.zip` bundles into `user://mods/`, and reports updates. Optional signature checking for curated content is a later milestone.

---

## 5. Content Schemas

All fields use `snake_case`. Names are i18n objects. IDs never change.

### 5.1 Element types (15) & type chart
`earth, fire, water, metal, crystal, air, electricity, light, dark, poison, martial, spirit, psionic, plant, neutral`.

```json
{ "id": "fire", "name": {"en": "Fire"}, "color": "#e04a1d" }
```

`type_chart.json` is a single effectiveness matrix keyed `attacker → target`:

```json
{ "chart": { "fire": { "plant": 2.0, "water": 0.5, "fire": 0.5 } } }
```

### 5.2 Taxonomies (breeding groups + bodyplan)
A species belongs to **1–3** taxonomies. They drive breeding compatibility, body plan rendering, and trait inheritance.

```json
{
  "id": "mammal",
  "name": {"en": "Mammal"},
  "bodyplan": "bipedal_quad",
  "breeding": {
    "compatible": ["humanoid", "beast"],
    "egg_steps": 5120,
    "offspring_rules": [{"if_second": "reptile", "then": ["reptile", "mammal"]}]
  },
  "traits": ["warm_blooded", "terrestrial"]
}
```

Base taxonomy set: `mammal, reptile, amphibian, fish, insect, arachnid, centipede, millipede, gastropod, cephalopod, bivalve, magnoliopsid, pinopsid, polypodiopsid, bryopsid, agaricomycete, saccharomycete, eurotiomycete, artificial`.

### 5.3 Terrain (`terrain.json`)
Battlefield cell properties and effects.

```json
{
  "hole":   {"blocks_move": true,  "fall": true},
  "lava":   {"blocks_move": false, "on_turn": "burn_damage"},
  "water":  {"blocks_move": false, "status": "soaked"},
  "tree":   {"blocks_move": true,  "cover": true, "block_los": true},
  "rock":   {"blocks_move": true,  "cover": true, "block_los": false}
}
```

### 5.4 Arenas / battlefields
Rectangular, futsal-field style: three **zones** — home side, neutral middle, enemy side. Size is per-arena (default **12 wide × 6 tall**, zones 4/4/4) and tuneable in data.

```json
{
  "id": "meadow_grid",
  "size": {"w": 12, "h": 6},
  "zones": {"home": {"cols": [0,3]}, "mid": {"cols": [4,7]}, "enemy": {"cols": [8,11]}},
  "spawn": {"home": [[1,2],[1,3]], "enemy": [[10,2],[10,3]]},
  "obstacles": [
    {"cell": [5,2], "terrain": "tree"},
    {"cell": [6,3], "terrain": "hole"}
  ],
  "palette": "meadow",
  "bgm": "battle_meadow.ogg"
}
```

Obstacles and terrain are authored per arena, so only some maps have hazards — "a plain field" and "a lava arena" are both just data.

### 5.5 Creature species
```json
{
  "id": "base:emberling",
  "dex_no": 1,
  "name": {"en": "Emberling"},
  "taxonomies": ["mammal"],
  "types": ["fire"],
  "stats": {"hp": 45, "atk": 60, "def": 40, "satk": 65, "sdef": 50, "spd": 45},
  "abilities": ["base:blaze"],
  "learnset": [
    {"stage": "baby", "level": 1, "move": "base:tackle", "require_records": []},
    {"stage": "juvenile", "level": 5, "move": "base:ember_blast"}
  ],
  "egg_moves": ["base:flame_charge"],
  "growth_stages": ["baby", "juvenile", "adult"],
  "sprite": {"bodyplan": "mammal", "palette": "emberling"},
  "behaviors": [
    {"behavior": "curl_up", "dex_unlocks": ["anatomy", "temperament"]},
    {"behavior": "hunts_dawn", "dex_unlocks": ["diet"]}
  ],
  "rideable": {"type": "land", "slots": 1},
  "base_aptitudes": {"farming": 0.5, "energy": 1.0, "gathering": 0.0},
  "craft_skills": {"woodworking": 0.6, "metalworking": 0.2, "cooking": 0.8},
  "stamina": {"max": 100, "recovery_rate": 0.15},
  "sanity": {"max": 100, "recovery_rate": 0.1},
  "catch_rate": 45,
  "growth_rate": "medium_fast"
}
```

`rideable` is **optional**: species without it cannot be mounts. `type` references `ride_types.json` and `slots` is how many riders fit (later multiplayer sidecar).

### 5.6 Moves
Grid battlefields → moves carry targeting, range, and area.

```json
{
  "id": "base:ember_blast",
  "name": {"en": "Ember Blast"},
  "type": "fire", "category": "special",
  "power": 70, "accuracy": 95, "priority": 0,
  "target": "cell", "range": 3, "area": "burst", "area_size": 1,
  "effect": [
    {"op": "damage", "scaling": "special"},
    {"op": "apply_status", "status": "burn", "chance": 0.15}
  ],
  "fx": "ember_blast_anim", "sound": "fire.wav"
}
```

### 5.7 Abilities
```json
{
  "id": "base:blaze",
  "name": {"en": "Blaze"},
  "trigger": "hp_threshold", "threshold": 0.33,
  "effect": [{"op": "damage_mult", "factor": 1.5, "if": "self.type == move.type && self.hp_pct < 0.33"}]
}
```

### 5.8 Effect library & pipeline
The **effect library** is the only code that lives in the content space. It ships a bounded set of verified ops: `damage, heal, drain, apply_status, stat_mod, multi_hit, recoil, field, weather, hazard, move_cell, swap_positions, shield, zone_effect, buff_stack, farm_drop, ...`.

Conditionals (`if`) and simple arithmetic are allowed; control flow that could desync is not. A mod *cannot* add ops; a genuinely new mechanic is a small framework PR adding one op — the documented extension path.

### 5.9 Variants (8 total)
Every creature instance carries a variant; **`normal` is variant #1**, so the full set is:

| # | Variant   | Visual                                                        | Stat effect                                                          | Origin                            |
|---|-----------|---------------------------------------------------------------|---------------------------------------------------------------------|-----------------------------------|
| 1 | normal    | base                                                          | none                                                                | wild / breeding / artificial      |
| 2 | albino    | almost all white                                              | none                                                                | wild / breeding                   |
| 3 | melanism  | almost all black                                              | none                                                                | wild / breeding                   |
| 4 | alpha     | bigger, battle scars                                          | +HP, +Speed, +1 species-dependent stat (slight)                     | wild (rare) / breeding            |
| 5 | mutant    | distinct visual mark, always                                  | different/hidden ability **or** normally-impossible move **or** color (multiple ok, not all 3) | wild (very rare) / breeding       |
| 6 | runt      | smaller                                                       | +Speed, sometimes +SpA; −Def, −SpD, −Atk                           | wild / breeding                   |
| 7 | giant     | much bigger                                                   | stronger in all senses; **much slower**                             | wild (very rare) / breeding       |
| 8 | hybrid    | always a strange artifact (bigger eyes, smaller tail, ...)    | moves normally unavailable (like egg moves)                       | breeding only / artificial build  |

```json
// variants.json entry
{
  "id": "alpha",
  "display_image_rule": "scale 1.2 + scar_overlay",
  "stat_deltas": {"hp": 1.25, "spd": 1.15, "extra": {"pool": 0.1, "pick": "species_note"}},
  "origins": ["wild", "breeding"]
}
```

Hybrid cannot appear in the wild; its "egg moves" and artifact come from data configured per species.

### 5.10 Natures
```json
{ "id": "brave", "name": {"en": "Brave"}, "up": "atk", "down": "spd" }
```

### 5.11 Items (and the three slots)
Each creature has **2 cosmetic slots** (hats, glasses, jewelry — zero effect) and **1 utility/combat slot** (weapons, armor, tools — real in/out-of-battle effects: terrain immunity, stat boosts, move modifiers).

```json
{
  "id": "base:heat_armor",
  "name": {"en": "Heat Armor"},
  "slot": "utility",
  "effects": [
    {"op": "terrain_immunity", "terrain": "lava"},
    {"op": "stat_mod", "stat": "def", "mult": 1.2}
  ]
}
```

Cosmetic effects: none — pure layered overlays (see §9).

### 5.12 Spheres (containers) & ball skins
Spherical storage devices (lost technology):

```json
{
  "id": "base:sphere_standard",
  "slot": "container",
  "stasis": true,
  "emergency_release": {"on_device_damage": true, "threshold": 0.2},
  "skin_slots": true
}
```

- Creatures in spheres are in **full stasis** — nothing exterior affects them and they can't sense/affect the outside.
- **Emergency policy**: on device damage or extreme circumstances the device auto-frees its creature (data-driven threshold).
- **Ball skins**: cosmetic customization of device appearance applied at towers for a material fee; visual only, relevant only to contests (capsules + stickers analogue).

### 5.13 Records (per-creature achievements)
History bytes stored **inside the creature's device**, shown in the creature summary. Independent of the player achievement system.

```json
{ "id": "champion_final", "name": {"en": "Champion Finalist"}, "trigger": "battle_finish:format:championship_finals" }
```

Record triggers: defeats, format/season participation, finals, streaks, etc. **Some records gate learnset entries and growth-stage transitions.**

### 5.14 Research / dex (behavior observation)
The dex does **not** auto-fill. Players deploy it in the wild and **observe behaviors** (Pokémon Snap–like); each observed behavior adds dex data. The only automatic fills are **variant data**, recorded at capture or birth.

```json
// behaviors.json
{ "species": "base:emberling", "behavior": "hunts_dawn", "dex_unlocks": ["diet", "activity"] }
```

### 5.15 Regions / maps / wild encounters / base tasks / base zones / underground
- **Regions/maps**: tilemap scene references (packed like any content), spawn points, tower locations, arena flags, and region-level unlocks (permissions, tools) plus **base zones** and **underground** entrances. Maps are scenes, but their *content* (encounters, layout refs, palettes, zones) is data.
- **Wild encounters**: `region + species + level range + weight + terrain/condition + variant_weights`.
- **Base tasks** (`base_tasks.json`): farming, energy generation, resource gathering, crafting assist, etc. Species declare `base_aptitudes`; assigning creatures to base tasks automates those activities. **Output scales with species aptitude × individual stats × bond** (bond multiplier defined in `balance.json`).
- **Base zones** (`base_zones.json`): the only buildable areas in a region. Each zone is a sandbox boundary (per-region: rect/polygon or map cells) plus the **unlock requirements**:
```json
{
  "id": "meadow_homestead_zone",
  "region": "base:meadow",
  "bounds": {"cells": [[14, 8], [14, 9], [15, 8], [15, 9]]},
  "permission": "base:meadow_homestead_permit",
  "tools_required": ["base:construction_tools"],
  "max_structures": 8, "max_plots": 4,
  "buildable_terrain": ["grass"], "climate": "temperate"
}
```
- **Underground** (`underground.json`): per-region exploration sub-world. Dig spots, mineral/resource nodes (with rates), hazards, and secret spaces. Structure:
```json
{
  "id": "meadow_underground",
  "region": "base:meadow",
  "entrances": [{"at": [18, 22]}],
  "dig_spots": [{"cell": [3, 5], "pool": "base:meadow_minerals", "respawn_days": 3}],
  "hazards": [{"cell": [7, 2], "terrain": "cave_hole"}],
  "secret_spaces": [{"cell": [9, 9], "unlock": "base:shovel"}]
}
```

### 5.16 Ride types & mount gear
`ride_types.json` categorizes the terrain a mount can traverse:

```json
{
  "land":  {"surfaces": ["grass", "dirt"], "speed_mult": 1.0},
  "water": {"surfaces": ["water"], "speed_mult": 1.0, "swim": true},
  "air":   {"surfaces": ["*"], "speed_mult": 1.5, "fly": true},
  "lava":  {"surfaces": ["lava"], "speed_mult": 0.9, "immune": true},
  "snow":  {"surfaces": ["snow", "ice"], "speed_mult": 0.9}
}
```

Riding requires a **crafted key item** matched to both the creature and ride type (bridles, mount chairs, etc.):

```json
{
  "id": "base:bridle_land",
  "slot": "gear",
  "ride_type": "land",
  "compatible": {"taxonomies": ["mammal", "reptile"]},
  "crafted_from": {"base:leather": 2, "base:metal_ingot": 1},
  "quality": {"bond_low": 0.6, "bond_high": 1.1}
}
```

Ride performance (speed, stability, terrain tolerance) is derived deterministically from the individual's **bond + relevant stats** and the gear's quality curve — no runtime RNG.

### 5.17 balance.json
Single tuning hub: EV budget, XP curves, catch-rate formula, damage formula constants, drop rates, base labor outputs, **friendly-fire base odds**, **bond scaling curves** (friendly fire, ride quality, base tasks), crop timers, construction costs, **ecosystem equilibrium thresholds**, **physics/chemistry interaction constants**, **crafting quality modifiers**.

### 5.18 Ecosystem & map layers
Every overworld map has **layers**. Layers are data-defined stacks that compose the visible world:

| Layer | Mutable? | Contents |
|---|---|---|
| **terrain** | no | desert, beach, grassland, snow, lava, water… (permanent per cell) |
| **topography** | no | elevation, slopes, cliff faces, cave ceilings |
| **vegetation** | yes | trees, bushes, herbs, fungi, tall grass, crops |
| **resources** | yes | mineral veins, ore nodes, clay deposits, gem seams |
| **structures** | yes | player-placed objects (fences, walls, chests, crafting stations) |

Players can alter the **vegetation**, **resources**, and **structures** layers freely within their base zone (and in the wild within ecosystem rules). They **cannot** change terrain type or topography — a desert stays a desert.

**Ecosystem equilibrium** (Wakfu-inspired): every harvestable node belongs to a **population pool** per map chunk. Harvesting removes from the pool; the pool regenerates over time tied to the region's `ecosystem.json`. The schema:

```json
{
  "meadow": {
    "chunks": {"0,0": {"trees": 12, "bushes": 20, "herbs": 30}},
    "regen": {"trees": {"per_hour": 0.003}, "bushes": {"per_hour": 0.006}, "herbs": {"per_hour": 0.01}},
    "overharvest_threshold": 0.2,
    "overharvest_effect": "barren",
    "restoration_items": ["base:fertilizer", "base:seedling"]
  }
}
```

If a chunk drops below the threshold (over-harvesting), the `barren` state triggers: no new growth, reduced spawns, visual degradation. Restoring the chunk requires player action (planting, fertilizing). This keeps the landmass stable across multiplayer while allowing detail-level freedom.

> **Multiplayer-safety contract for ecosystem (normative).** The ecosystem is the highest-contention shared state in the game, so it is scoped under an **authoritative, delta-replicated, deterministic-as-view** design. Normative rules §5.18a–§5.18i below; the enforcement/consistency design is detailed in [TRD.md §7](./TRD.md) and the persistence/network payloads in [DATA_SCHEMA.md](./DATA_SCHEMA.md).

#### 5.18a Authoritative single owner
Each map **chunk** has exactly **one authoritative owner** — the server that owns the region map (seed map), or, in offline single-player, a deterministic **local-only authority** that treats the saved chunk like a server would. Clients never directly mutate chunk population; they send **harvest/plant intents**, and the authority applies deltas.

#### 5.18b State is chunk-scoped and coarse
Replication granularity is the **chunk** (`region:chunk_coord`), not the individual node. Shared state is only the population ints + the `barren` boolean + a `mutation_seq` counter. Individual nodes, trees, and ore placements are **derived renders**, re-seeded deterministically from the chunk population (below), so they never need to be synced or stored.

#### 5.18c No RNG anywhere in shared state
All regrowth is **time-integrator based**, not random. A chunk stores only `population[resource]` and `last_regen_tick`. The current population is a pure function:
`population(t) = clamp(pop + ∫ regen_rate dt, 0, cap)`. No floats — regen is accumulated in **integer ticks** (a fixed gametime step). Two clients or a client and the server compute identical numbers from the same `(pop, last_tick)`, so the body ("barren", node layout) is identical and verification is cheap.

#### 5.18d Deterministic node layout
From a chunk's integer population, node placement is derived by a **seeded spatial hash** over `(region_id, chunk_coord, resource, population, seed)`. The same inputs always render the same trees/ores. The seed is part of the map definition and modset, so layout is identical across peers without transferring coordinates.

#### 5.18e Intents, deltas, and final authority
- Client interacting with a node sends `IntentHarvest { node_key, tool, count }` / `IntentPlant { resource, count }`.
- Authority validates rules (owned chunk, tool, population > 0, not barren for plant-restricted), applies the delta, and broadcasts `Mutation { chunk, resource, new_pop, seq, tick, actor }`.
- The client **previews optimistically** in its own view and reconciles against the authoritative `Mutation` (rollback-and-apply on mismatch). Only the authority can publish `barren` transitions.

#### 5.18f Mutation ordering & conflict
Applied in strict `(seq, tick, actor_id)` order. A single mutation sequence per chunk prevents races. If two actors target the same chunk the same simulation tick, the authority serializes by actor id. Ties never resolve by client-supplied state.

#### 5.18g Verification & anti-abuse
- Client-supplied intents carry **only** unambiguous facts (a node exists at key, a species of a tool). The client never claims "population just rose" — that is always recomputed server-side.
- Rate limits per actor per chunk; over-harvest to `barren` triggers the ecosystem rules and is a global-consistency event, not a local claim.
- Because shared state is coarse ints, a checksum of `(chunk, pop, seq, tick)` is cheap to include in saves and validation.

#### 5.18h Crafting/player-owned state is separate
Nodes and structures **inside a player's claimed base zone** are player-owned, not chunk-population-owned. They use the normal save/ownership flow (see §5.15 base zones, DATA_SCHEMA), and are exempt from the shared ecosystem pool (they neither drain nor feed it) — this keeps bases out of MP contention.

#### 5.18i Mods stay data-only & deterministic
`ecosystem.json` exposes only rates, caps, thresholds, and effect names. A mod adds a resource type → new ints in every chunk; framework computes them identically. No mod code runs in the replication path.

### 5.19 Physics & chemistry engine
Elemental moves interact with the overworld **outside of battle** — a data-driven simulation layer:

| Move type | Overworld effect | Condition |
|---|---|---|
| fire | ignite campfire, power forge, warm creature | target: flammable object or station |
| water | fill container, extinguish fire, irrigate crop | target: container or fire or crop plot |
| cold + water | freeze water surface, create ice path | climate < threshold |
| electric | power machine, light area | target: compatible device |
| metal (defensive) | weakened effectiveness | climate > hot_threshold |
| electric (offensive) | unfocused / spread | rain or water terrain |
| plant | accelerate crop growth, regenerate vegetation | target: crop or barren chunk |
| earth | create barrier, shift loose debris | target: open cell |
| air | push objects, spread seeds | target: movable object |
| spirit | reveal hidden nodes, calm wild creatures | target: hidden area or creature |

Physics interactions are defined in `physics_rules.json`:

```json
{
  "fire_ignite": {
    "trigger": {"move_type": "fire", "target_tag": "flammable"},
    "effect": "burn",
    "duration": "until_extinguished",
    "spread": {"to": "adjacent_flammable", "chance": 0.1}
  },
  "water_fill": {
    "trigger": {"move_type": "water", "target_tag": "container"},
    "effect": "fill",
    "result": "base:water_container"
  },
  "cold_freeze": {
    "trigger": {"move_type": "water", "climate_below": 0},
    "effect": "transform",
    "result_terrain": "ice_path",
    "duration": "5_minutes_real"
  },
  "current_drift": {
    "trigger": {"object": "movable", "on_terrain": "water"},
    "effect": "drift_downstream",
    "carry_to": "connected_river_cell",
    "carry_across_maps": true
  }
}
```

Objects (tree trunks, rocks, containers) can be **pushed, pulled, carried** by water currents, wind, or creature moves — and can travel across map connections (a river on map A feeds map B). This is the "push a log into a river and it floats downstream" mechanic.

### 5.20 Crafting system
Crafting is intentionally layered and realistic. Three tiers:

| Tier | Requirement | Example |
|---|---|---|
| **hand** | resources only, not in battle | rope, simple bandage, water container |
| **tool** | tool equipped in player or creature slot | planks (saw), metal ingot (hammer + tongs) |
| **station** | crafting station with worker slots | chair (woodworking bench + saw + hammer + glue + screws) |

**Recipe chains**: most items require other crafted items as ingredients. A chair needs planks (wood → saw → woodworking bench) + glue (animal fat + ash → cooking pot) + screws (metal ingot → forge + anvil) + fasteners. Chains are data-defined:

```json
{
  "id": "base:chair",
  "name": {"en": "Chair"},
  "tier": "station",
  "station": "base:woodworking_bench",
  "ingredients": [
    {"item": "base:planks", "count": 4},
    {"item": "base:glue", "count": 1},
    {"item": "base:screws", "count": 6},
    {"item": "base:nails", "count": 4}
  ],
  "tools_required": ["base:saw", "base:hammer", "base:ruler"],
  "craft_skills": {"woodworking": 0.5},
  "quality_curve": {"skill_bonus": 0.3, "station_bonus": 0.2, "creature_bonus": 0.2}
}
```

**Crafting stations** have **2 worker slots**: one for the player, one for a creature. Player and creature can work simultaneously for faster/better results, or either can work alone. Station schema:

```json
{
  "id": "base:woodworking_bench",
  "name": {"en": "Woodworking Bench"},
  "worker_slots": 2,
  "compatible_skills": ["woodworking"],
  "tools_slots": 3,
  "power_source": "manual",
  "base_station": true
}
```

Station `power_source` can be `manual`, `creature`, `electric`, `thermal`, `water` — so creatures or environmental systems (fire-powered forge, water-powered mill) can drive them.

**Automation**: creatures at bases can operate stations autonomously (player assigns creature → station → recipe). Output = creature `craft_skills` × individual stats × bond × stamina/sanity. Creatures with zero stamina **stop working**; creatures with low sanity **make errors** or **refuse**.

### 5.21 Creature labor: stamina, sanity, and capabilities
Species declare `stamina` and `sanity` caps and recovery rates. These drive how long a creature can work before rest:

```json
{
  "stamina": {"max": 100, "recovery_rate": 0.15, "work_drain": 0.05},
  "sanity": {"max": 100, "recovery_rate": 0.1, "work_drain": 0.02}
}
```

- **Stamina**: drains while working; hits 0 → creature rests automatically (cannot be forced). Recovery is time-based (at base or in sphere).
- **Sanity**: drains slowly; low sanity → reduced quality, chance of errors, chance of refusal. High bond slows sanity drain; high bond also restores sanity faster when resting.
- **Craft skills**: per-species aptitudes (e.g. `{"woodworking": 0.6, "metalworking": 0.2, "cooking": 0.8}`). Only skills ≥ a recipe's `craft_skills` threshold allow the creature to attempt that task. Skill value affects quality and speed.

---

## 6. Creature DNA & Stat Math

### 6.1 The six stats + instance state
Main stats: **HP, Speed (Spe), Physical Attack (Atk), Physical Defense (Def), Special Attack (SpA), Special Defense (SpD)**.

Per individual:
- 4 **move slots**, 1 **ability slot**
- **IV set** — unique per instance, immutable, set at spawn/birth.
- **EV set** — trainable hidden stats.
- **Nature**, **variant**, **growth stage**, **bond** (tamed/captured + level)
- **records**, **lineage** (breeding), **ball type**, **stamina** & **sanity** (labor/mood values), **craft skills** (species data), optional per-instance flags.

### 6.2 EV system
EVs boost a stat by up to **+100% of its base**. A global **budget** (`B`, default 200 percent-points, in `balance.json`) caps the total: 2 stats maxed, ~67% across 3, ~34% across 6, or any mixed combination ≤ budget with per-stat cap 100%.

### 6.3 DNA encoding
`CreatureDNA` is a versioned, ID-only compact text:
```
<version>:<species_id>:<stage>:<level>:<exp>:<nature>:<moves[4]>:<ability>:
<iv[...] >:<ev[...]>:<variant>:<bond>:<records[...]>:<lineage>:<ball>:<flags>
```
Same blob for **save files, trading, network sync, and future franchise games**. A version byte enables migrations forever. No floats; everything integer or ID.

---

## 7. Growth Stages (the "evolution" rework)

- **Permanent.** Stages never revert. Represented as an ordered list on the species (`baby → juvenile → adult → …`).
- Transitions are triggered by data: age/exp thresholds + optional required **records**, items, or conditions.
- Stages change stats, size `scale`, learnsets, and visible assets — aging rather than transformation.
- **Death exists** (unlike Pokémon). Defined circumstances (falling into a hole, certain hazards/effects, rare battle outcomes, story events) permanently remove a creature. Death conditions are data, stored per-stage/per-terrain/per-effect so modders control how hardcore their content is.
- Attached to each stage: accessible `learnset` entries (some records-gated), `base_aptitudes` for base labor, and appearance.

---

## 8. Battle System

- **Formats:** 1v1 and 2v2 (per battle, set by arena/rules). Party size is **6**; the squad is picked before battle.
- **Battlefield:** rectangular grid, default **12×6**, split into **home / mid (neutral) / enemy** zones. Spawn cells per zone; obstacles and terrain per arena.
- **Flow:** command phase (move / item / swap / reposition between zones) → deterministic resolution phase (priority → speed order → effect pipelines with seeded RNG).
- **Positioning matters:** moves have `target / range / area`; **cover** (trees/rocks) blocks line-of-sight and ranged attacks, granting protection; terrain hazards (holes → fall out/damage, lava → burn) interact with moves, effects, and utility items (e.g. heat armor grants immunity).
- **Friendly fire is the default.** Area, burst, and line effects roll a per-ally hit chance (data-defined per move/effect). The individual's **bond** reduces that chance on a curve from `balance.json` (`friendly_fire_chance = base_friendly_fire × (1 − bond_factor)`), reaching 0 at high bond. Abilities/effects may suppress friendly fire for specific cases.
- One engine drives wild, trainer, and (later) online battles; all rules are data.

---

## 9. Appearance Pipeline (the "shiny" equivalent)

Composable layered rendering, all data-driven:

```
base sprite (species bodyplan + species palette)
  → variant layer   (palette override: albino/melanism; scar/tint: alpha/mutant;
                     scale: alpha/runt/giant; artifact overlay: hybrid)
  → utility item    (weapon/armor/tool overlay)
  → cosmetic 1 / cosmetic 2
```

Each layer resolves to a data rule (palette map or overlay asset) via the **asset resolver**. A mod extends any layer without touching code — e.g. a new variant or a new hat is just JSON + a png.

---

## 10. World, Taming vs Capturing, Riding, Storage, Bases & Underground

### 10.1 Overworld
Top-down 2D tilemaps built from **layers** (§5.18): terrain (immutable), topography (immutable), vegetation (harvestable/plantable), resources (harvestable), structures (player-placed). The spawner reads wild encounter tables; taming takes patience and observation; the dev can flag areas for 1v1/2v2. Terrain surfaces carry a ride type (land/water/lava/snow/…) so movement rules are data. Elemental moves interact with the environment via the physics/chemistry engine (§5.19): fire ignites, water fills, cold freezes, currents carry objects downstream across connected maps.

### 10.2 Tamed vs captured
- **Tamed:** grows faster, bonds more easily — but earns the player's trust the hard way.
- **Captured:** grows slower and bonds slower, but starts on the team immediately.
- Battle potential is identical; only leveling/bond curves differ (data-driven growth-rate modifiers).

### 10.3 Riding & mounts
- A species is a mount only if its data declares `rideable` (ride type + slots).
- To ride, the player must **own** the creature (tamed or captured) **and** own the **crafted mount gear** matched to that creature's taxonomy and ride type (`ride_gear.json`; requires materials, e.g. leather + metal ingot).
- Ride performance is deterministic from the individual's **bond + stats** and the gear's quality curve: speed, stability, and terrain tolerance. Air/water/lava/snow types unlock traversal the player can't do on foot.
- Mounts are real party members: they can be dismounted into battle without baggage; riding simply uses their overworld movement rules.

### 10.4 Spheres & towers
- Spheres impose stasis; emergency release on device damage (data-driven).
- **Towers:** pocket-dimension storage (the PC analogue), breeding lab, and sphere skin customization (material fee). Towers unlock **superficial dex-map data** for the region (no map pins — flavor only).

### 10.5 Bases & farming
Bases are **sandboxes** — but governed by strict rules:

- **Claim system.** To establish a base, the player uses a **claim item** (e.g. `base:territory_marker`) on a designated **base zone** cell. This delimits the buildable area (data from `base_zones.json`: rect/polygon cells, max structures, max plots, buildable terrain, climate).
- **Unlock + permission.** Placing a claim requires (1) crafting/unlocking the claim item (key item) and (2) earning the **region's building permit** (quest/currency unlock). Both are per-region.
- **Sandbox construction.** Within the claimed area, players freely place and arrange structures, plots, decorations, storage, and **crafting stations** (checking `max_structures`/`max_plots` and `buildable_terrain`). Structures are persistent and saved.

**Crafting at base:**
- Crafting stations (woodworking bench, forge, cooking pot, etc.) are placed inside the base like any structure.
- Each station has **2 worker slots**: 1 player + 1 creature. Both can work simultaneously (faster, better quality), or either alone.
- The player configures a station by assigning a creature + selecting a recipe. The creature's `craft_skills`, stamina, and sanity determine capability.
- **Stamina**: drains while working; at 0 the creature rests automatically (cannot be forced). Recovery is time-based at the base or in a sphere.
- **Sanity**: drains slowly; low sanity → reduced quality, errors, or refusal. High bond slows drain and speeds recovery.
- **Automation**: once configured, the creature works autonomously on the assigned recipe. The player can leave and return to collected output. Output quality = `craft_skills` × stats × bond × stamina_factor × sanity_factor.

**Farming:**
- Crop plots are grid cells with data-defined crops: planting, growth phases, watering, harvest.
- Region `climate`/terrain and configured crop timers drive growth. Crops can be irrigated with water-type moves (physics/chemistry engine, §5.19).
- Yield feeds materials, cooking/crafting, and the economy.
- Farming can also be automated by stationed creatures (farming aptitude × stats × bond).

**Ecosystem rules apply inside bases too** — players can harvest vegetation/resources within their claimed area, but the ecosystem equilibrium (§5.18) still governs regrowth and over-harvesting consequences. Per §5.18h, nodes/structures *inside* the claim are player-owned (exempt from the shared pool), while unclaimed wilderness nodes remain chunk-population-governed.

Base state persists in saves and respects multiplayer ownership rules later.

### 10.6 Underground
A per-region exploration sub-world (4th/5th-gen inspired) that encourages ranging off the beaten path:

- **Entrances** at data-defined map cells lead to a separate underground grid generated from `underground.json`.
- **Dig spots & resource nodes** yield minerals/materials on a respawn schedule; pools and rates are data (same ecosystem equilibrium rules as surface, §5.18).
- **Hazards** (cave holes, gas pockets) reuse the terrain/effect system — including the same danger rules as battle terrain. Physics/chemistry interactions apply: fire moves illuminate dark areas, water moves create pools, cold freezes underground streams.
- **Secret spaces** reward tools such as a shovel and act as optional outposts/storage.
- Underground and surface share the creature/encounter tables where configured, so exploration there also yields wild finds.

---

## 11. Save System & Cross-Game Foundation

- Save = player state + party + DNA list + research log + progression + base assignments + base zones/plots/buildings + claimed territories + crafting stations + inventory + owned ride gear/tools + **player-authored world edits inside claims** (exempt from shared ecosystem pool).
- **Shared ecosystem chunk state (region population ints + seq + tick) is NOT player save data** — in MP it is server-authoritative; in offline SP it is stored once alongside the local region authority (see §5.18, DATA_SCHEMA). Keeping it out of the player save is what makes it MP-safe and migration-free.
- DNA's stable, versioned, ID-only format is the shared asset of the whole connected franchise: creatures transfer between games carrying their history; medals/rewards from one game unlock features elsewhere.

---

## 12. Multiplayer

**MP-safe foundation, single-player first.**
- Battles are deterministic (seeded RNG + fixed order) so networked battles resolve identically everywhere.
- Networking is data-defined: a **content-manifest handshake** pins the exact modset for a room/match; servers reject mismatched modsets.
- Trades = DNA exchange only.
- **World/ecosystem state is authoritative and delta-replicated** under the contract in §5.18a–§5.18i: chunk-scoped coarse ints, time-integrator regrowth (no RNG), deterministic node derivation, intent→delta→broadcast with strict ordering and verification. See [TRD.md §7](./TRD.md) for enforcement and [DATA_SCHEMA.md](./DATA_SCHEMA.md) for payloads.
- Netcode is additive (M9), not a rewrite of the SP engine; the deterministic data model above is what makes that true.

---

## 13. Milestones

- **M0 — Foundations:** framework skeleton, ModManager (zip + folder), manifest + schema validation, ContentRegistry, i18n, base-mod layout. *Gate: a JSON mod registers a type + a creature.*
- **M1 — Battle core:** effect ops, grid + zones + terrain + cover, 1v1/2v2 resolution, seeded determinism, damage formula.
- **M2 — Authoring pipeline:** 15 types + full chart, taxonomies, core moves/abilities, creatures, 8 variants, appearance pipeline, content tester + packager. *Gate: an outsider authors a loadable creature zip without the editor.*
- **M3 — World:** overworld, taming vs capturing, spheres + emergency release, towers, party + summary UI, **riding + mount gear**.
- **M4 — Progression & sandbox:** growth stages (permanent), EV/IV/nature, records, research/dex, breeding via taxonomies, friendly-fire/bond, save + migration, **death rules**.
- **M5 — Bases, crafting & automation:** claim tool + permits, base zones, layered world (terrain/topography immutable, rest mutable), ecosystem equilibrium, crafting chains + stations + 2 worker slots, creature labor (stamina/sanity/craft skills) automation.
- **M6 — Physics & chemistry engine:** elemental move interactions, freezing/softening/spreading, water-current object transport across maps, desert water-fill, campfire/forge, machine power.
- **M7 — Underground:** dig spots, resource nodes with ecosystem regrowth, secret spaces, hazards.
- **M8 — Mod manager + store UI:** enable/disable, dependencies/conflicts, validation errors, browse/download/update.
- **M9 — MP-forward:** deterministic battle sync, DNA trading, content-manifest handshake, authoritative synchronized world/ecosystem state under §5.18a–§5.18i.

---

## 14. Risks & Tradeoffs

- **Data-only ceiling:** a mechanic the ops can't express needs a small framework PR. Mitigated by the composable pipeline + a documented "add an op" path.
- **Trust/cheating:** data-only mods are cheap to validate; PvP can pin modsets.
- **Web export:** filesystem restrictions around zip/cache need care (export-P1 item, not a blocker).
- **Death design:** needs player-facing protection (clear signposting, UI warnings) — flagged as a deliberate design risk given Pokémon's conventions.
- **Ecosystem balancing:** over-harvest vs regeneration needs careful tuning to avoid griefing/barren maps; restoration items are the mitigation.
- **Creature labor depth:** stamina/sanity/capabilities are content-heavy to author per species; the framework must ship good defaults and strong validation.
- **Physics engine scope:** full Skyrim/BotW-level interaction is aspirational; v1 ships the bounded, data-driven rule set in `physics_rules.json`, extensible by mods.
- **AI-friendly authoring:** plain JSON + schemas makes the `godot_ai` addon, MCP, and CLI first-class content tooling.

---

## 15. Extension Path (TL;DR for contributors)

| I want to add...            | I do...                                                          |
|-----------------------------|------------------------------------------------------------------|
| a creature, move, variant   | drop a JSON (or zip it) into `user://mods/`                      |
| a ride type / mount gear    | JSON in `ride_types.json` / `ride_gear.json` + item & sprite     |
| a new effect op             | framework PR in `addons/phylaworld/battle/effect_library/`        |
| a base task / ball skin     | JSON in `base_tasks.json` / `items.json` + optional sprite        |
| a base zone / underground   | JSON in `base_zones.json` / `underground.json` + map cells        |
| an ecosystem / physics rule | JSON in `ecosystem.json` / `physics_rules.json`                   |
| a recipe / crafting station | JSON in `crafting.json` / `crafting_stations.json`                |
| a whole new region          | scene + JSON region/encounter/arena/base_zone/ecosystem data      |
| a translation               | edit the i18n objects in any content file                         |