# Phylaworld — Backend & Data Schema

> **Purpose:** The full, precise definition of every data structure — content files, instance state (DNA), persistence, the network/sync payloads for the multiplayer-safe systems, plus quests, achievements, telemetry, and player customization. This is the authoritative source for field types; behavioral rules live in [TRD.md](./TRD.md), design intent in [ARCHITECTURE.md](./ARCHITECTURE.md) and [PRD.md](./PRD.md).
> **Format:** Every structure is defined as **JSON** (the runtime/persistence format) and, where useful, a **JSON Schema** snippet (the validation contract). GDScript loads these with `JSON.parse_string()`. No TypeScript forms are used.
> **Conventions:**
> - JSON field names are `snake_case`. Types are JSON-native: `"string"`, `"integer"`, `"number"` (fixed-point ints at runtime, see TR-6), `"boolean"`, `"object"`, `"array"`, `"null"`. `?` after a name = optional; absent default noted where relevant.
> - `i18n` = object of locale→text, e.g. `{"en":"Fire","es":"Fuego"}`; resolved by locale code at runtime.
> - All content ids are **stable full ids** `"modid:itemid"`; renaming is a new id (ARCHITECTURE law 3).
> - Unknown keys are rejected by the schema validator.
> - **Meta/telemetry fields** (`meta`, `history`, `flags`, `counters`) reconcile per [TRD.md](./TRD.md) TR-45..TR-49: they are append-only/aggregate data, deterministic, and excluded from gameplay-determinism inputs.

---

## 1. Directory of Schema Files

| File (res://content/<mod>/) | Kind | Contents |
|---|---|---|
| `manifest.json` | manifest | mod metadata, deps, content list |
| `balance.json` | balance | global tuning constants |
| `types.json` / `type_chart.json` | types / type_chart | 15 elemental types + effectiveness matrix |
| `taxonomies.json` | taxonomies | breeding groups + bodyplan + breeding rules |
| `terrain.json` | terrain | battlefield/overworld cell terrain + effects |
| `arena.json` | arenas | battlefield grids (zones, obstacles) |
| `moves.json` | moves | moves (type/category/power/effect pipeline) |
| `abilities.json` | abilities | ability triggers + effect pipelines |
| `statuses.json` | statuses | status conditions + effects |
| `natures.json` | natures | stat +/- pairs |
| `variants.json` | variants | the 8 variants (normal first) |
| `species/*.json` | species | per-species creature definitions |
| `growth_stages.json` | growth_stages | stage order/rules |
| `items.json` | items | slots, spheres, gear, materials |
| `ride_types.json` / `ride_gear.json` | ride_types / ride_gear | mount terrain types + mount gear |
| `records.json` | records | per-creature achievements/gates |
| `behaviors.json` | behaviors | research/dex observation entries |
| `crafting.json` / `crafting_stations.json` | crafting / crafting_stations | recipes + stations (worker slots) |
| `base_tasks.json` | base_tasks | automatable labor tasks |
| `base_zones.json` | base_zones | designated buildable areas + permits |
| `ecosystem.json` | ecosystem | chunk pools, regen, thresholds |
| `physics_rules.json` | physics_rules | elemental move ↔ world interactions |
| `map_layers.json` | map_layers | layered world definition |
| `quests.json` / `achievements.json` | quests / achievements | story/adventure objectives + meta achievements |
| `customization.json` / `cosmetics.json` | customization / cosmetics | player avatar + creature cosmetics |
| `modes.json` | modes | player flags/counters kind table |
| `regions.json` / `wild_encounters.json` / `underground.json` | regions / encounters / underground | world + spawns + underground |

---

## 2. Manifest

```json
{
  "id": "my_mod",
  "name": {"en": "My Mod"},
  "version": "1.0.0",
  "author": "asdf",
  "description": {"en": "..."},
  "dependencies": ["base"],
  "conflicts": [],
  "content": ["content/types.json", "content/species/emberling.json"]
}
```

| Field | Type | Notes |
|---|---|---|
| `id` | string | `^[a-z][a-z0-9_]*$` |
| `name` | i18n | required |
| `version` | string | semver `"x.y.z"` |
| `author` / `description` | string? / i18n? | optional |
| `dependencies` / `conflicts` | array\<string\>? | mod ids |
| `content` | array\<string\>? | relative paths; defaults to walking `content/` |

---

## 3. Content Schemas (core kinds)

> Each content file may define one object or an array of objects (batching). Objects carry `"$kind"` (or live in a kind-specific file) to route to the right validator.

### 3.1 Types
```json
{
  "$kind": "types",
  "id": "fire",
  "name": {"en": "Fire"},
  "color": "#e04a1d"
}
```
```json
{ "$kind": "type_chart", "chart": { "fire": { "plant": 2, "water": 0.5, "fire": 0.5 } } }
```

### 3.2 Taxonomies (breeding + bodyplan)
```json
{
  "id": "mammal",
  "name": {"en": "Mammal"},
  "bodyplan": "bipedal_quad",
  "breeding": {
    "compatible": ["humanoid"],
    "egg_steps": 5120,
    "offspring_rules": [{"if_second": "reptile", "then": ["reptile","mammal"]}]
  },
  "traits": ["warm_blooded"]
}
```

### 3.3 Terrain
```json
{
  "key": "hole",
  "blocks_move": true,
  "fall": true,
  "cover": false,
  "block_los": false,
  "on_turn": "burn_damage",
  "status": "burn",
  "ride_ok": []
}
```

### 3.4 Arena
```json
{
  "id": "meadow_grid",
  "size": {"w": 12, "h": 6},
  "zones": {"home": {"cols": [0,3]}, "mid": {"cols": [4,7]}, "enemy": {"cols": [8,11]}},
  "spawn": {"home": [[1,2],[1,3]], "enemy": [[10,2],[10,3]]},
  "obstacles": [{"cell": [5,2], "terrain": "tree"}],
  "palette": "meadow",
  "bgm": "battle_meadow.ogg",
  "format": "1v1"
}
```
`size` = w/h ints; `zones.*.cols` = `[first,last]`; `Cell` = `[x,y]` integer pair.

### 3.5 Species
```json
{
  "id": "base:emberling",
  "dex_no": 1,
  "name": {"en": "Emberling"},
  "taxonomies": ["mammal"],
  "types": ["fire"],
  "stats": {"hp":45,"atk":60,"def":40,"satk":65,"sdef":50,"spd":45},
  "abilities": ["base:blaze"],
  "learnset": [{"stage":"baby","level":1,"move":"base:tackle","require_records":[]}],
  "egg_moves": ["base:flame_charge"],
  "growth_stages": ["baby","juvenile","adult"],
  "sprite": {"bodyplan":"mammal","palette":"emberling"},
  "behaviors": [{"behavior":"curl_up","dex_unlocks":["anatomy"]}],
  "rideable": {"type":"land","slots":1},
  "base_aptitudes": {"farming":0.5,"energy":1.0,"gathering":0},
  "craft_skills": {"woodworking":0.6,"metalworking":0.2,"cooking":0.8},
  "stamina": {"max":100,"recovery_rate":0.15,"work_drain":0.05},
  "sanity": {"max":100,"recovery_rate":0.1,"work_drain":0.02},
  "catch_rate": 45,
  "growth_rate": "medium_fast"
}
```
`stamina`/`sanity` have `{"max":int,"recovery_rate":number,"work_drain"?:number}`.

### 3.6 Move
```json
{
  "id": "base:ember_blast",
  "name": {"en": "Ember Blast"},
  "type": "fire",
  "category": "special",
  "power": 70,
  "accuracy": 95,
  "priority": 0,
  "pp": 15,
  "target": "cell",
  "range": 3,
  "area": "burst",
  "area_size": 1,
  "effect": [
    {"op":"damage","scaling":"special"},
    {"op":"apply_status","status":"burn","chance":0.15}
  ],
  "fx": "ember_blast_anim",
  "sound": "fire.wav"
}
```
`effect` = array of effect-op objects; ops enumerated by the framework `effect_library`.

### 3.7 Ability
```json
{
  "id": "base:blaze",
  "name": {"en": "Blaze"},
  "trigger": "hp_threshold",
  "params": {"threshold": 0.33},
  "effect": [{"op":"damage_mult","factor":1.5}]
}
```

### 3.8 Variant (8 total, "normal" first)
```json
{
  "id": "alpha",
  "display_image_rule": "scale 1.2 + scar_overlay",
  "stat_deltas": {"hp":1.25,"spd":1.15},
  "origins": ["wild","breeding"],
  "color_overrides": [],
  "artifact": ""
}
```
`id` ∈ normal, albino, melanism, alpha, mutant, runt, giant, hybrid. `origins` ∈ wild/breeding/artificial/hybrid_only.

### 3.9 Growth Stage
```json
{
  "id": "adult",
  "name": {"en": "Adult"},
  "stat_mult": {"hp":1.2},
  "scale": 1.0,
  "learnable": ["base:ember_blast"],
  "base_aptitudes": {"farming":0.5},
  "death_sources": ["hole_fall","lava"]
}
```

### 3.10 Item (slots: cosmetic/utility/container/gear/material)
```json
{
  "id": "base:heat_armor",
  "name": {"en": "Heat Armor"},
  "slot": "utility",
  "effects": [{"op":"terrain_immunity","terrain":"lava"}],
  "skin": {"slots": true},
  "emergency_release": {"on_device_damage": true, "threshold": 0.2},
  "crafted_from": {"base:leather":2},
  "quality": {"bond_low":0.6,"bond_high":1.1}
}
```

### 3.11 Ride types & gear
```json
{ "id": "air", "surfaces": ["*"], "speed_mult": 1.5, "fly": true }
```
```json
{
  "id": "base:bridle_land",
  "slot": "gear",
  "ride_type": "land",
  "compatible": {"taxonomies":["mammal","reptile"]},
  "crafted_from": {"base:leather":2,"base:metal_ingot":1},
  "quality": {"bond_low":0.6,"bond_high":1.1}
}
```

### 3.12 Record (per-creature achievement/gate)
```json
{ "id": "champion_final", "name": {"en": "Champion Finalist"}, "trigger": "battle_finish:format:championship_finals" }
```

### 3.13 Behavior (research/dex)
```json
{ "species": "base:emberling", "behavior": "hunts_dawn", "dex_unlocks": ["diet","activity"] }
```

### 3.14 Crafting recipes & stations
```json
{
  "id": "base:chair",
  "name": {"en": "Chair"},
  "tier": "station",
  "station": "base:woodworking_bench",
  "ingredients": [
    {"item":"base:planks","count":4},
    {"item":"base:glue","count":1},
    {"item":"base:screws","count":6},
    {"item":"base:nails","count":4}
  ],
  "tools_required": ["base:saw","base:hammer","base:ruler"],
  "craft_skills": {"woodworking":0.5},
  "quality_curve": {"skill_bonus":0.3,"station_bonus":0.2,"creature_bonus":0.2},
  "output_slot": 0,
  "output": [{"item":"base:chair","count":1}]
}
```
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
Recipes form a **DAG** (`ingredients` reference other recipes' outputs); cycles are rejected at load (TR-26). `tier` ∈ hand/tool/station. `output` is the materialized result.

### 3.15 Base task
```json
{ "id": "base:gather_wood", "skill": "gathering", "output": {"base:wood":1}, "rate_key": "gather_wood" }
```

### 3.16 Base zone
```json
{
  "id": "meadow_homestead_zone",
  "region": "base:meadow",
  "bounds": {"cells": [[14,8],[14,9],[15,8],[15,9]]},
  "permission": "base:meadow_homestead_permit",
  "tools_required": ["base:construction_tools"],
  "max_structures": 8,
  "max_plots": 4,
  "buildable_terrain": ["grass"],
  "climate": "temperate"
}
```

### 3.17 Ecosystem
```json
{
  "meadow": {
    "chunks": {"0,0": {"trees":12,"bushes":20,"herbs":30}},
    "regen": {"trees":{"per_hour":0.003},"bushes":{"per_hour":0.006},"herbs":{"per_hour":0.01}},
    "overharvest_threshold": 0.2,
    "overharvest_effect": "barren",
    "restoration_items": ["base:fertilizer","base:seedling"]
  }
}
```
MP-safe contract in TR-16..24 / ARCHITECTURE §5.18.

### 3.18 Physics rule
```json
{
  "id": "current_drift",
  "trigger": {"object":"movable","on_terrain":"water"},
  "effect": "drift_downstream",
  "result": "",
  "duration": "",
  "spread": {"to":"adjacent_flammable","chance":0.1},
  "carry_to": "connected_river_cell",
  "carry_across_maps": true
}
```

### 3.19 Map layers
```json
{
  "layers": [
    {"name":"terrain","mutable":false},
    {"name":"topography","mutable":false},
    {"name":"vegetation","mutable":true},
    {"name":"resources","mutable":true},
    {"name":"structures","mutable":true}
  ]
}
```

### 3.20 Quests / missions
Story & adventure objectives. Structured for the quest ledger.

```json
{
  "id": "base:meadow_intro",
  "name": {"en":"A Friend in the Wild"},
  "kind": "main",
  "parent": "",
  "giver": "base:npc_professor",
  "unlock_conditions": [
    {"flag":"tutorial_finished","eq":true}
  ],
  "objectives": [
    {"id":"tame","type":"tame_creature","target":"base:emberling","count":1},
    {"id":"craft_ball","type":"craft_item","target":"base:sphere_standard","count":1}
  ],
  "completion_rewards": {
    "items":[{"item":"base:sphere_standard","count":3}],
    "permit":"base:meadow_homestead_permit",
    "set_flags":["base:quest_settlement_done"]
  },
  "fail_conditions": [],
  "repeatable": false,
  "meta": {"cooldown_days":0}
}
```

| Field | Type | Notes |
|---|---|---|
| `id` | string | full id |
| `kind` | string | main / side / daily / event / tutorial |
| `parent` | string? | optional parent quest id |
| `giver` | string? | npc id |
| `unlock_conditions` | array\<condition\> | availability gate |
| `objectives` | array\<objective\> | progress-tracked goals |
| `completion_rewards` | object? | items / permit / exp / set_flags / counters |
| `fail_conditions` | array\<condition\>? | optional fail triggers |
| `repeatable` | boolean | default false |
| `meta` | object? | cooldown etc. |

**Condition object** (shared by unlock/fail/achievement): `{"flag"|"counter"|"quest"|"item"|"species"|"variant": ..., "op":"eq|ne|gte|lte|gt|lt|contains", "value": ...}`.

**Objective object**: `{"id":str, "type":objective_type, "target":id?, "count":int, "progress_flag"?:str, "progress_counter"?:str}`. Objective types are data keys (tame_creature, craft_item, defeat, capture, observe_behavior, ride_distance, gather, build, etc.).

### 3.21 Achievements (meta/account-level)
```json
{
  "id": "base:steps_100k",
  "name": {"en":"A Hard Walker"},
  "description": {"en":"Walk 100,000 steps."},
  "hidden": false,
  "condition": {"counter":"steps_walked","op":"gte","value":100000},
  "rewards": {"items":[{"item":"base:badge","count":1}],"xp":500},
  "unlocks": ["base:title_walker"],
  "meta": {"category":"exploration"}
}
```

### 3.22 Customization & cosmetics
Player avatar and creature cosmetic setups.

```json
{
  "$kind": "customization",
  "avatar_layers": ["skin","hair","eyes","outfit_top","outfit_bottom","shoes","accessories","emote"],
  "palette_ids": ["base:skin_palettes","base:hair_palettes"],
  "preset": {
    "skin":"base:skin_warm",
    "hair":"base:hair_short",
    "hair_color":"#2b1c12",
    "eyes":"base:eyes_round",
    "eyes_color":"#3b6b9e",
    "outfit_top":"base:shirt_plains",
    "outfit_bottom":"base:pants_travel",
    "shoes":"base:boots_leather",
    "accessories":["base:glasses_round"],
    "emote":"base:emote_wave"
  }
}
```
```json
{ "id": "base:glasses_round", "name": {"en":"Round Glasses"}, "layer":"accessories", "slot":"head", "tintable":true, "path":"assets/cosmetics/glasses_round.png" }
```

| Structure | Purpose |
|---|---|
| `customization.json` | avatar layer order + default presets |
| `cosmetics.json` | individual cosmetic/accessory items (layer, slot, tintable, asset) |
| `palettes.json` | named color palettes for skin/hair/clothes |

Creature customization (the 2 cosmetic slots + utility slot, §5.11) reuses `items.json` with `slot` fields; the layered renderer is ARCHITECTURE §9.

---

## 4. Instance & Runtime State

### 4.1 CreatureDNA (persist / trade / network — single string)
```
<dna_v>: <species_id> <stage> <level> <exp> <nature>
         <move_0> .. <move_3> <ability>
         iv[hp atk def satk sdef spd] ev[hp atk def satk sdef spd]
         <variant> <bond> <records:csv> <lineage:str> <ball>
         <stamina> <sanity> <flags>
```
- All fields ids or ints; no floats (TR-6). Version prefix enables migration (TR-7).
- `bond`, `stamina`, `sanity` are ints in a fixed scale (persisted only at rest majority; labor drains persisted).
- Records append-only (see §4.3).

### 4.2 Derived stats (computed, not stored)
`stat = floor((base * stage_mult) * (1 + iv_pct) * (1 + nature_up/down) + ev_factor)`
- Base + stage_mult + IV + nature + EV; budget per §6.2 fixed-point.

### 4.3 Records (per-creature, device-stored achievements)
```json
{ "at": 412345, "type": "battle_win", "detail": {"format":"1v1","opponent":"trainer_x"} }
```

### 4.4 Craft progress (runtime)
```json
{
  "station": "base:woodworking_bench",
  "recipe": "base:chair",
  "player_slot": "player_uid",
  "creature_slot": "dna_ref",
  "progress": 55,
  "speed": 23,
  "quality": 82,
  "output_slot": {"item":"base:chair","count":1}
}
```

---

## 5. Persistence Model

### 5.1 Player Save (`user://saves/<profile>/save.json`)
```json
{
  "ver": 1,
  "checksum": "sha256...",
  "gametime": 412345,
  "player": {
    "uid": "player_uid",
    "region": "base:meadow",
    "map_cell": [14,8],
    "appearance": {"skin":"base:skin_warm","hair":"base:hair_short","hair_color":"#2b1c12","eyes":"base:eyes_round","eyes_color":"#3b6b9e","outfit_top":"base:shirt_plains","outfit_bottom":"base:pants_travel","shoes":"base:boots_leather","accessories":["base:glasses_round"],"emote":"base:emote_wave"},
    "flags": {"tutorial_finished": true, "settlement_intro_done": false},
    "counters": {"steps_walked": 4120, "battles": 34, "battles_won": 27, "creatures_caught": 12, "tames_done": 5}
  },
  "party": ["dna_ref_1","dna_ref_2"],
  "dex": {"observed_behaviors": {...}, "variant_seen": {...}},
  "quests": {"active": ["base:meadow_intro"], "completed": [], "objectives": {"base:meadow_intro.tame": 1}},
  "achievements": {"unlocked": ["base:steps_100k"]},
  "progression": {"permits": ["base:meadow_homestead_permit"], "tools_unlocked": ["base:construction_tools"]},
  "breeding": {...},
  "inventory": [{"item":"base:wood","count":12}],
  "claims": [{"zone":"base:meadow_homestead_zone","cells":[...]}],
  "base": {"plots": [...], "buildings": [...], "crafting_stations": [...], "assignments": [...]},
  "owned_ride_gear": ["base:bridle_land"],
  "research_log": {...},
  "telemetry": {"battle_history": [...], "trade_history": [...]}
}
```

#### Player flags & counters (drives achievements/quests)
```json
{
  "flags": {
    "tutorial_finished": true,
    "first_capture": true
  },
  "counters": {
    "steps_walked": 4120,
    "battles": 34,
    "battles_won": 27,
    "creatures_caught": 12,
    "tames_done": 5,
    "battles_lost": 7,
    "rides": 3,
    "distance_ridden": 2100,
    "craft_items": 8,
    "collect_species": 12
  }
}
```
- **flags** = unordered boolean set (achievement/quest gates). **counters** = monotonic aggregates, updated by game systems, not setpoints. Both reconcile per TR-45/TR-46 (deterministic increments, server-validated deltas).
- Any new flag/counter must be registered in the kind table `modes.json` so schemas/viz know it.

- **Player-authored world edits** (inside claims) live with `base`; exempt from the shared ecosystem pool (§5.18h).
- **Shared ecosystem chunk state is NOT in the player save** (TR-16/TR-23): in MP it is server-side; in offline SP it lives in a separate local region-authority store (§5.4).

### 5.2 Trade history & telemetry records
```json
{
  "trade_history": [
    {
      "trade_id": "uuid",
      "utc_ts": 1725300000,
      "gametime": 412345,
      "from_player": "player_uid_a",
      "to_player": "player_uid_b",
      "dna_hash": "sha256_of_dna",
      "dna_summary": {"species":"base:emberling","level":12,"variant":"normal","iv_total":45},
      "item": {"item":"base:sphere_standard","count":1},
      "result": "completed",
      "client_ver": "1.0.0",
      "modset": {"base":"1.0.0"}
    }
  ]
}
```
Trade metadata is **append-only**; a server admin/dev can analyze volume, species flow, and anomalies. DNA itself stays ID-only for the gameplay exchange; the hash+summary give telemetry without duplicating full DNA.

### 5.3 Fixed-point & no floats
All numeric persistence is int or fixed-point (integer value + stored scale constant in `balance.json`).

### 5.4 Offline region authority store (`user://world/<region>.worldstate`)
```json
{
  "chunks": [
    {"region":"base:meadow","cx":0,"cy":0,"pop":{"trees":12},"last_regen_tick":1000,"barren":false,"seq":3,"seed":77}
  ]
}
```
Offline mirror of server-authoritative chunk store; identical shape (TR-17).

---

## 6. Network / Sync Payloads

> All payloads are JSON; numeric state fixed-point ints. Content-manifest handshake (TR-51) precedes any gameplay sync. Every request/response carries optional `meta` (telemetry: `utc_ts`, `client_ver`, `modset`, `session_id`, `event_id`) — see §6.5.

### 6.1 Content manifest handshake
```json
{ "cmd": "hello", "client_mods": {"base":"1.0.0","my_mod":"1.0.0"}, "meta": {"utc_ts":1725300000,"client_ver":"1.0.0","session_id":"s1"} }
```
```json
{ "cmd": "welcome", "accepted": true, "pinned_modset": {"base":"1.0.0"}, "missing": [], "extra": [], "server_seed_epoch": 77 }
```
- Reject if client modset ≠ pinned (TR-51).

### 6.2 Ecosystem protocol (normative, TR-20/TR-21)
```json
{ "chunk": ["base:meadow",0,0], "resource": "trees", "node_key": "tree_37", "tool": "base:axe", "count": 1, "at_tick": 1000 }
```
```json
{ "chunk": ["base:meadow",0,0], "resource": "trees", "count": 1, "at_tick": 1000 }
```
```json
{ "chunk": ["base:meadow",0,0], "resource": "trees", "new_pop": 11, "barren": false, "seq": 4, "tick": 1001, "actor_id": "player_uid_a" }
```
- Ordering: `(seq, tick, actor_id)` (TR-21). Client preview-optimistic then reconcile.

### 6.3 Trade (DNA only) with metadata
```json
{
  "trade_id": "uuid",
  "cmd": "trade_offer",
  "from_player": "player_uid_a",
  "to_player": "player_uid_b",
  "dna_hash": "sha256",
  "dna_summary": {"species":"base:emberling","level":12,"variant":"normal"},
  "item": {"item":"base:sphere_standard","count":1},
  "meta": {"utc_ts":1725300000,"client_ver":"1.0.0","modset":{"base":"1.0.0"},"session_id":"s1","event_id":"e1"}
}
```
- No gameplay state beyond the DNA/item exchange (TR-52); metadata is telemetry-only and non-authoritative for gameplay.

### 6.4 Battle replay sync
```json
{
  "seed": 173451,
  "modset": {"base":"1.0.0"},
  "arena": "base:meadow_grid",
  "format": "1v1",
  "squad_a": ["dna_ref_1"],
  "squad_b": ["dna_ref_2"],
  "meta": {"utc_ts":1725300000,"client_ver":"1.0.0","session_id":"s1","region":"base:meadow"}
}
```
- Outcome fully determined by transcript (TR-9/TR-53).

### 6.5 Telemetry envelope (all commands: battle, trade, world, global-challenge, etc.)
```json
{
  "meta": {
    "utc_ts": 1725300000,
    "client_ver": "1.0.0",
    "modset": {"base":"1.0.0"},
    "session_id": "s1",
    "event_id": "e1",
    "region": "base:meadow",
    "device": "linux"
  }
}
```
Requirements (TR-47..TR-49):
- **Telemetry is append-only and never alters gameplay-determinism inputs.**
- Server may aggregate for admins: DAU, trade volume, species flow, quest-completion funnels, ecosystem-health metrics, performance.
- Field names are stable (no renames); additions are additive.
- Player PII is kept minimal (numeric counters + hashed ids); raw narrative strings only in quest text, never in telemetry.

---

## 7. Global Constants (`balance.json`, fixed-point)

| Key | Type | Purpose |
|---|---|---|
| `ev_budget` | integer | total EV percent-points (200) |
| `ev_cap_per_stat` | integer | max % per stat (100) |
| `friendly_fire_base` | number | base ally-hit chance (fixed-point) |
| `bond_factor_curve` | object\<int,number\> | friendly-fire/ride/labor scaling |
| `xp_curves` | object\<str,array\<int\>\> | growth-rate level thresholds |
| `catch_formula` | object | capture constants |
| `damage_constants` | object | damage formula |
| `regen_scale` | integer | gametime ticks/sec for ecosystem |
| `stamina` / `sanity` | object | labor curves |
| `craft_quality` | object | quality_curve constants |
| `crop_timers` | object | growth/watering |
| `construction_costs` | object | base structure costs |
| `quest_timeouts` | object | daily/event quest reset windows |

---

## 8. JSON Schema Example (species, abridged)

> Schemas live at `addons/phylaworld/data/schemas/*.schema.json` (draft-07), mirror every kind, and power the lint CLI, editor plugin, MCP tool, and mod-store validation.

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["id","dex_no","name","taxonomies","types","stats","growth_stages"],
  "properties": {
    "id": {"type":"string","pattern":"^[a-z][a-z0-9_]*:[a-z][a-z0-9_]*$"},
    "dex_no": {"type":"integer","minimum":1},
    "name": {"type":"object"},
    "taxonomies": {"type":"array","items":{"type":"string"},"minItems":1,"maxItems":3},
    "types": {"type":"array","items":{"type":"string"},"minItems":1,"maxItems":2},
    "stats": {
      "type":"object",
      "required":["hp","atk","def","satk","sdef","spd"],
      "properties": {
        "hp":{"type":"integer"}, "atk":{"type":"integer"}, "def":{"type":"integer"},
        "satk":{"type":"integer"}, "sdef":{"type":"integer"}, "spd":{"type":"integer"}
      }
    },
    "growth_stages": {"type":"array","items":{"type":"string"}},
    "catch_rate": {"type":"integer"},
    "growth_rate": {"type":"string"}
  },
  "additionalProperties": false
}
```

---

*The PRD governs intent, the TRD governs behavior, and this document governs the exact data. Data changes require a schema version bump; behavioral changes require a TRD update.*