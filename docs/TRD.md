# Phylaworld — Technical Requirements Document (TRD)

> **Purpose:** Concrete, implementable requirements for the engineering systems. Where the [PRD](./PRD.md) says *what* and [ARCHITECTURE.md](./ARCHITECTURE.md) says *how*, the TRD specifies **exact inputs, outputs, invariants, protocols, and limits** a developer must satisfy. This is the contract between design and code. Covers mod loading, battle, physics, ecosystem MP-safety, crafting/labor, riding, research, **quests/achievements, telemetry/operability**, the mod store, and multiplayer.
> **Normative references:** [PRD.md](./PRD.md), [ARCHITECTURE.md](./ARCHITECTURE.md), [DATA_SCHEMA.md](./DATA_SCHEMA.md). When a requirement disagrees with data, the **DATA_SCHEMA trumps**; when behavior disagrees with the schema, the **TRD trumps**; intent disputes resolve to the PRD.

---

## 1. Requirements & Traceability Conventions

- Each requirement has a stable id: `TR-[n][-suffix]`.
- Each requirement states its **priority**: `MUST` (blocking), `SHOULD` (recommended), `MAY` (optional).
- Where a requirement has an acceptance check, it is written as `AC:` with concrete, testable statements.
- Requirement ids are referenced by PRD feature ids (FR-*) and ARCHITECTURE sections (§) for traceability.

---

## 2. Mod Loading & Content Registry

### TR-1 Mod discovery (`FR-MD1.1`, §4.3)
- **MUST** scan `user://mods/` at boot (and on refresh) for both `.zip` files and loose folders.
- A valid mod directory/archive root contains `manifest.json`.
- **AC:** A `.zip` and a folder with identical content load the same registry entries.

### TR-2 Manifest parsing & validation (`FR-MD1.4`)
- **MUST** parse `manifest.json` with a per-field schema. On any failure, the mod is **disabled** and a structured error is raised.
- Errors MUST carry: `mod_id`, `file`, `field_path`, `expected`, `got`, `message`.
- Required fields: `id`, `name`, `version`. Optional: `author`, `description`, `dependencies`, `conflicts`, `content[]`.
- `id` MUST be `^[a-z][a-z0-9_]*$` (lowercase, no spaces).
- **AC:** Loading `my_mod` with a missing `id` produces an actionable error, not a crash.

### TR-3 Content discovery (`FR-MD1.1`)
- The `content[]` list enumerates relative `res://`-style paths (`content/types.json`). If absent, **MUST** walk the mod's `content/` directory for `*.json`.
- Each file is routed by a **kind discriminator field** (`"$kind": "types" | "type_chart" | ...`) or by a registered filename mapping.
- **AC:** Adding a `content/creatures/foo.json` is picked up without editing the manifest.

### TR-4 Registry indexing ($4/§5)
- ContentRegistry indexes by `kind` and full id `"{mod_id}:{item_id}"`.
- **MUST** reject (skip + report) duplicate full ids across active mods; resolution order is data (override order) chosen by the player.
- Cross-file references MUST resolve lazily or in topologically sorted order across dependencies.
- **AC:** A creature referencing a move from a dependency mod loads only after the dependency registers.

### TR-5 Determinism of load
- Loading MUST be deterministic: same modset → same registry state, regardless of filesystem order. Sort by `(mod_id, kind, item_id)`.

---

## 3. Data & State Integrity

### TR-6 No floats in serialized state (`NFR-3`, §6.3)
- All persisted/networked numeric state is **integer or fixed-point** (scale stored where needed).
- `balance.json` may render human decimals but the runtime serializes fixed-point ints.
- **AC:** A property fuzzer over any saved state finds zero floating-point literals.

### TR-7 DNA encoding (`FR-C1.1`, §6.3, DATA_SCHEMA)
- `CreatureDNA` is a single UTF-8 string, version-prefixed, ID-only.
- Encode/decode MUST be symmetric (round-trip == original).
- Unknown version is rejected; migration path is a registered per-version transform.
- **AC:** `decode(encode(x)) == x` for all valid DNA; a v0 DNA migrates to latest without data loss.

### TR-8 Save integrity (`NFR-3`)
- Saves are atomic (write-temp-then-rename), checksummed, and versioned.
- Corrupt or foreign-version saves are quarantined, never silently overwritten.

---

## 4. Content Schemas & Validation

- **MUST** expose each kind's JSON schema for tooling (lint CLI, editor plugin, MCP).
- `json` schema files live in `addons/phylaworld/data/schemas/*.schema.json`.
- Every schema enforces: known keys only, correct types, full-id uniqueness, and referential integrity where possible at load.
- **AC:** `phylaworld lint --mod user://mods/X` exits non-zero listing every violation with path+field.

---

## 5. Battle Engine

### TR-9 Deterministic resolution (`FR-B1.6`, §8)
- Battle uses a single seeded RNG instance; every effect consumes from it in strict sequence.
- The seed + modset version are recorded with the battle.
- **AC:** Same seed + modset + identical command log → identical full battle transcript (replay).

### TR-10 Turn & resolution order (§8)
- Command phase collects player actions. Resolution phase orders: priority → per-formula speed → effect pipeline.
- Reposition and item use consume the same command budget as a move unless the format says otherwise.
- **AC:** A unit test asserts priority beats speed beats initiative ties deterministically.

### TR-11 Friendly fire & bond (`FR-B1.5`)
- Friendly-fire chance per target ally: `p_ff = clamp(base_ff * (1 - bond_factor(bond)), 0, base_ff)`.
- `base_ff` and `bond_factor` come from `balance.json`; both computed in fixed-point.
- **AC:** At `bond_factor >= 1.0` friendly fire is exactly 0; at bond 0 it equals `base_ff`.

### TR-12 Terrain & cover (`FR-B1.4`, §5.3)
- Terrain effects and cover (block move / block LoS / damage/status) are pure data lookups; battle code contains no per-terrain special cases.
- A move's `range`/`area` are validated against the arena grid; invalid targets are rejected at command time.
- **AC:** Adding a new terrain kind is a JSON edit with no framework change.

---

## 6. Physics / Chemistry Engine

### TR-13 Rule evaluation (`FR-PH1.3`, §5.19)
- All overworld move↔world interactions are entries in `physics_rules.json`.
- A single deterministic evaluator matches `(move_type, target_tag, state)` → effect; no bespoke per-move code.
- **AC:** Adding `fire_ignite`-style rule is JSON-only; unit-testable against a known cell state.

### TR-14 Object transport (`FR-PH1.2`)
- Objects carry a `movable` tag and current `(map, cell)`; water current/wind/moves apply drift via `current_drift` rules.
- Cross-map movement follows declared map adjacency (a river exit/entry pair).
- Movement is deterministic; positions resolve to the same cells for a given state.
- **AC:** A log pushed into a river reaches the connected downstream map's declared catch cell.

### TR-15 Climate-dependent type behavior (`FR-PH1.1`)
- Climate is per-region data; type effects (cold freezing water moves, heat softening metal defense, electric unfocused on rain/water) are data predicates over climate + weather state.
- **AC:** In a region flagged cold, an eligible water move transforms to ice per the rule; identical in SP and MP.

---

## 7. Ecosystem — Multiplayer-Safe Contract (normative)

> This is the designed enforcement of ARCHITECTURE §5.18a–§5.18i. It is the strictest section because ecosystem state is the highest-contention shared world data.

### TR-16 Authority model
- Each chunk `(region_id, cx, cy)` has exactly one authoritative owner.
  - **SP offline:** a local region authority in the save; it plays the same role a server would.
  - **MP:** the server owning that region map is the authority.
- Clients hold **replicas**; they never own shared population.
- **AC:** Two writers to the same chunk in MP both observe the authority's final value; no client can raise population locally.

### TR-17 Replicated state shape
- Minimum shared per chunk: `population[resource:int]`, `last_regen_tick:int`, `barren:bool`, `mutation_seq:int`, `seed:int` (from map definition).
- Everything visible (tree placement, ores) is **derived** from these ints (§5.18d), not stored.
- **AC:** Chunk serializes to a fixed small tuple; adding no nodes appears in the shared blob.

### TR-18 Time-integrator regrowth (no RNG)
- `population(t) = clamp(floor(pop0 + regen_rate * elapsed_ticks), 0, cap)`.
- `regen_rate` and `cap` are per-resource uint from `ecosystem.json`; elapsed computed in integer gametime ticks.
- **AC:** For equal `(pop0, last_tick, now)`, client and server compute equal integers (property test).

### TR-19 Deterministic node layout
- Node positions = seeded spatial hash over `(region, cx, cy, resource, population, seed)`.
- **AC:** Same tuple → identical node set; changing population changes layout deterministically, no RNG.

### TR-20 Intent → delta → broadcast
- Client sends `IntentHarvest { chunk, resource, node_key, tool, count }` or `IntentPlant { chunk, resource, count }`.
- Authority: validate (ownership, tool, pop>0, barren for restricted plant), apply delta, publish `Mutation { chunk, resource, new_pop, barren, seq, tick, actor_id }`.
- Client applies optimistic preview, reconciles on mutation (rollback+apply on mismatch).
- **AC:** A forged "population+100" from a client is ignored; authority value wins.

### TR-21 Ordering & conflict
- Applied in `(seq, tick, actor_id)` order; chunk has a single monotonic `seq`.
- Same-tick two-actor conflicts serialize by `actor_id`. Never by client-claimed state.
- **AC:** Concurrent intents at the same tick converge for all observers.

### TR-22 Anti-abuse & verification
- Client intents carry only verifiable facts (node exists at key, tool present). Client never asserts population.
- Rate limits per `actor_id` per chunk per tick window.
- A cheap checksum `(chunk, pop, seq, tick)` guards saves and validation.
- **AC:** Abusing harvest rate triggers the rate-limit path and a server-authoritative correction.

### TR-23 Player-owned vs shared split
- Nodes/structures inside a claimed base zone are **player-owned** state (exempt from the pool; normal save flow). Unclaimed wilderness is chunk-population-governed.
- **AC:** Base-placeable resources do not appear in or mutate the chunk shared tuple.

### TR-24 Mod determinism
- `ecosystem.json` exposes only rates/caps/thresholds/effect names. A new resource adds ints computed identically by the framework. No mod code in the replication path.
- **AC:** A mod adding `"rare_ore"` replicates/builds identically with zero framework change.

---

## 8. Crafting & Creature Labor

### TR-25 Crafting tiers (`FR-CR1.1`)
- Recipe resolution: `hand` (resources only, not in battle) → `tool` (tool equipped) → `station` (station + usually tools).
- **AC:** A `station`-tier recipe without its station or an equipped required tool is rejected with the missing ingredient/tool listed.

### TR-26 Recipe chain resolution (`FR-CR1.2`)
- `crafting.json` is a directed acyclic graph of recipe→ingredient; cycles are rejected at load.
- A recipe is craftable iff all ingredients and tools/station are present.
- **AC:** Load fails on a cyclic recipe with the cycle reported.

### TR-27 Worker slots & cooperation (`FR-BA1.7`)
- Stations declare `worker_slots` (fixed 2 by default: 1 player + 1 creature).
- When both slots occupied, progress rate and quality use the combined bonus formula (DATA_SCHEMA `craft_progress`).
- **AC:** Player+creature on the same recipe yields faster and/or higher quality than either alone, matching the formula.

### TR-28 Stamina / Sanity (`FR-CR1.4`)
- Work drains stamina every tick; at `stamina == 0` creature **rests** (cannot be forced to work; auto-resume when recovered).
- Work drains sanity; below `sanity_err_threshold` quality drops and error/refusal chance rises (fixed-point, deterministic).
- High bond slows sanity drain and speeds recovery (data curves, fixed-point).
- **AC:** A stamina-0 creature is unassignable until rested; an unhappy creature deterministically makes the same quality result for a given state.

### TR-29 Craft skills gating (`FR-CR1.5`)
- A creature can attempt a recipe only if its `craft_skills[skill] >= recipe.craft_skills[skill]`.
- Skill value affects speed and quality via `quality_curve`.
- **AC:** A creature below the threshold cannot be assigned; above it, output follows the quality formula.

### TR-30 Automation (`FR-BA1.5`)
- Assignment = `station → recipe → creature`. Creature works autonomously until item completes, stamina hits 0, or it refuses.
- Output persists into station `output_slots`; player collects on return.
- **AC:** An autonomous craft with sufficient stamina/sanity completes and deposits the item; interrupted stamina leaves partial progress saved.

---

## 9. Riding

### TR-31 Riding gating (`FR-R1`)
- Ride allowed iff: creature `rideable` matches, player owns matching crafted gear (`ride_gear.json`) for `(taxonomy, ride_type)`.
- **AC:** Without owning the gear, mount is blocked with a clear localized message; with it, mount succeeds.

### TR-32 Ride performance (`FR-R1.4`, §10.3)
- `speed = base_speed(ride_type) * gear_quality(bond, stats)`; stability and terrain tolerance likewise from bond+stats.
- Deterministic; no runtime RNG.
- **AC:** Two identical creatures+gear produce identical ride metrics.

---

## 10. Research / Dex

### TR-33 Behavior observation (`FR-D1.1`)
- Dex data unlocks only via observing a species' `behaviors` while the dex is deployed.
- Variant data auto-fills at capture/birth only.
- **AC:** Never observing → no species dex entry; capturing only fills variant row.

---

## 11. Quests, Missions, Achievements

### TR-40 Quest data model (`FR-STORY1`, §3.20 DATA_SCHEMA)
- Quests are pure data (`quests.json`): `id`, `kind` (main/side/daily/event/tutorial), `objectives[]`, `unlock_conditions[]`, `completion_rewards`, `fail_conditions[]`.
- **AC:** Adding a new quest is a JSON edit; the quest ledger runs it with zero framework changes.
- Objective types are registered keys (tame_creature, craft_item, defeat, capture, observe_behavior, ride_distance, gather, build, …); an unknown type is a schema error.

### TR-41 Objective & condition evaluation (`FR-STORY1.3`)
- Objective progress is stored per `(quest_id, objective_id)` as an integer counter or flag and advanced only by deterministic game-system events.
- A **condition** `{flag|counter|quest|item|species|variant, op, value}` is a pure predicate over player state (DATA_SCHEMA §3.20).
- **AC:** Taming the exact target species increments exactly that objective once; already-satisfied objectives do not re-award.

### TR-42 Completion & rewards (`FR-STORY1.4`)
- On all objectives complete, the quest transitions to `completed`, rewards (items/permits/xp/set_flags/set_counters) are applied exactly once, and the quest is added to `completed[]` (dedup guard).
- **AC:** Completing a quest twice applies rewards once; a completed quest cannot be re-started unless `repeatable`.

### TR-43 Achievements (`FR-META1`, §3.21 DATA_SCHEMA)
- Achievements are meta/account-level predicates over the **player flag/counter store** (TR-47) plus quest/collection state.
- Unlocked achievements are recorded with a timestamp; hidden achievements reveal only after unlock.
- **AC:** A `steps_walked >= 100000` achievement unlocks exactly once when the counter crosses the threshold, and never re-fires.

### TR-44 Daily/event quest windows (`FR-STORY1.5`)
- Daily/event quests reset on a server-authoritative or local timetabled window from `balance.json` `quest_timeouts`; rewards are clamped to the window.
- Offline SP uses local gametime; MP uses server gametime to prevent window gaming.
- **AC:** A daily quest completed at 23:59 and 00:01 yields separate rewards in SP; MP users cannot harvest a window twice via clock manipulation locally.

### TR-45 Player flag & counter store (`FR-META2`, §5.1 DATA_SCHEMA)
- Two player-state stores: **flags** (unordered boolean set, e.g. `tutorial_finished`) and **counters** (monotonic integer aggregates, e.g. `steps_walked`, `battles`, `battles_won`).
- Flags/counters are updated only by game systems (deterministic increments), never by arbitrary client writes.
- In MP, counter increments are server-validated deltas; the authoritative total lives server-side and is replicated.
- Every flag/counter is registered in `modes.json` (kind table) for schema/viz/tooling.
- **AC:** A client cannot set `battles_won` to an arbitrary large number; only the server-applied deltas advance it.

### TR-46 Aggregates across sessions (`FR-META2.2`)
- Player-owned counters persist in the save (survive relog) and reconcile with any server-side copy by taking the max of validated deltas, never by summing whole-history re-uploads that could double count.
- **AC:** Relogging preserves counter totals; a resync does not double-count events already recorded.

---

## 12. Telemetry & Operability

### TR-47 Telemetry envelope (`FR-TEL1`, §6.5 DATA_SCHEMA)
- Every network command and notable single-player event carries a `meta` envelope: `utc_ts`, `client_ver`, `modset`, `session_id`, `event_id`, optional `region`.
- **AC:** A trade/battle/world command serializes its `meta` block and it round-trips verbatim.

### TR-48 Append-only, non-authoritative (`FR-TEL2`)
- Telemetry is **append-only** and **never** feeds gameplay-determinism inputs (TR-9/TR-20 stay pure; telemetry is written downstream). Field names are stable; additions are additive only.
- Tragedy avoided: a buggy telemetry value must not change a battle outcome or ecosystem value.
- **AC:** Fuzzing telemetry fields leaves determinism property tests untouched (green).

### TR-49 Admin/dev value (`FR-TEL3`)
- Server aggregates telemetry for ops/dev: DAU, trade volume & species flow (TR-52 request logs), quest-completion funnels (TR-40), ecosystem-health metrics (TR-18), and performance.
- Identifiers are hashed/opaque; PII is minimized (counters/ids, no raw narrative in telemetry).
- **AC:** An admin dashboard query returns trade volume and top-flowing species for a region/window from the telemetry store.

---

## 13. Mod Store & Tooling

### TR-50 Store client (`FR-MD1.3`)
- Fetches `index.json`; lists mods; downloads `.zip` to `user://mods/`; reports updates. Uses atomic write + content checksum.
- **MAY** verify signatures for curated content (post-v1).
- **AC:** A download interrupted mid-write leaves no partial mod in the active set.

### TR-56 Packager CLI (`FR-MD1.5`)
- `phylaworld pack <dir> <out.zip>` bundles manifest + content + assets deterministically (stable ordering, normalized paths).
- **AC:** Packing the same folder twice yields byte-identical zips.

---

## 14. Multiplayer (additive, M9)

- **TR-51** Content-manifest handshake pins exact modset+version per room/match (`FR-M1.2`).
- **TR-52** Trades are DNA-only exchange via device-to-device payload (`FR-M1.1`); trade telemetry is recorded per TR-47/TR-49 without duplicating full DNA into gameplay state.
- **TR-53** Battle sync replays from deterministic transcript (`FR-M1.3`, TR-9).
- **TR-54** World sync follows the ecosystem contract (TR-16–TR-24).
- **TR-55** Player flag/counter state and quest/achievement progress synchronize via authoritative server deltas (TR-45/TR-46).

---

## 15. Non-Functional Requirements Traceability

| NFR | TRs |
|---|---|
| Determinism | TR-5,9,10,18,19,20,28,32 |
| Mod safety (no code) | TR-2,3,4,24,50 |
| Save integrity | TR-6,7,8 |
| Quest/achievement integrity | TR-40,41,42,43,44,45,46 |
| Telemetry safety (non-authoritative) | TR-47,48,49 |
| Accessibility | (UI requirements in PRD; no TR here) |
| Performance | TR-17 (coarse state) |
| Platform limits | TR-50 (atomic write), TR-1 |

---

*Normative references: [DATA_SCHEMA.md](./DATA_SCHEMA.md) overrides field types; this TRD overrides behavioral wording; [ARCHITECTURE.md](./ARCHITECTURE.md) and [PRD.md](./PRD.md) provide design intent.*