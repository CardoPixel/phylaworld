# Phylaworld — Product Requirements Document (PRD)

> **Product:** Phylaworld — a pixel art, top-down 2D multiplayer world where creatures are tamed, studied, trained, and fought in turn-based battles.
> **Doc status:** Living document. Requirements here describe *what* the product must do and *why*; the [ARCHITECTURE.md](./ARCHITECTURE.md) describes *how* it is built. When they conflict, this document wins on intent; ARCHITECTURE wins on implementation.
> **Product pillars:** Creature collection & training · Turn-based tactical grid battles · Exploration & underground · Taming vs capturing · Breeding via taxonomy · Riding & mounts · Farming & bases · Research-driven dex · Mod-first content · Cross-game creature universe.

---

## 1. Vision

Phylaworld is a community-first, AI-friendly creature game where every player forges a personal history with unique individuals: tame them from the wild, study their behavior, train them, breed generations, ride them across varied terrain, build and automate bases with their labor — and battle strategically on tactical grid arenas where positioning, hazards, and bond matter as much as type matchups.

It is the *mainline* game of a connected franchise. A creature is a persistent, portable identity; a player's collection carries across future games and applications.

## 2. Goals & Non-Goals

### Goals
- **G1.** Make every creature instance feel unique (DNA: IVs, EVs, nature, variant, bond, records).
- **G2.** Deliver deep, tactics-first turn-based battles (grid, zones, terrain, cover) for 1v1 and 2v2.
- **G3.** Make the game **radically extensible**: anyone can author content with text files + a zip — no editor, no code.
- **G4.** Reward exploration: overworld travel, riding, and an underground sub-world.
- **G5.** Support both solitary play (tamed/captured progression) and social play (trading, bases, challenges, multiplayer).
- **G6.** Provide long-horizon meta: research, records, growth stages, breeding, bases/farming.
- **G7.** Keep multiplayer as an additive layer over a deterministic, mod-safe single-player core.

### Non-Goals (v1)
- **NG1.** No manual level-gating of content creation; mod content loads at runtime.
- **NG2.** No code execution from mods (data-only). Novel mechanics are framework PRs.
- **NG3.** Not a pure "cosmetic-only" personalization game: cosmetic depth is real, but utility items and loyalty matter more.
- **NG4.** No platform support commitment for iOS/macOS (community welcome).
- **NG5.** No auto-filling dex: research is earned through observation, not captures.

## 3. Players & Personas

| Persona | Profile | Core needs |
|---|---|---|
| The Collector | Loves variants, rare mutants/hybrids, shinies. | Variant depth (8 kinds), breeding, trading. |
| The Tactician | Competitive battler. | Deterministic grid PvP, records, friendly-fire/bond meta. |
| The Explorer / Photographer | Likes wilds, dex, scenery. | Research observation, ride exploration, underground. |
| The Farmer / Builder | Base-building, resource loops. | Designated base zones, farming, automation with creatures. |
| The Modder | Creates content for others. | Text-file authoring, packaging, store, validation. |
| The AI Assistant / Contributor | Builds content/tooling programmatically. | Plain JSON + schemas, lint/test/package tooling. |

## 4. Platforms

- **v1:** Windows, Linux, Android, Web.
- **Engine/tooling:** Godot 4.x, Aseprite (sprites), open-source everything.

---

## 5. Core Loop

```
Explore a region (overworld / riding / underground)
   → observe behaviors with the dex (research data)
   → encounter wild creatures → tame OR capture
   → train (battles, EVs), grow (stages), bond, breed (taxonomies)
   → battle in grid arenas (1v1 / 2v2)
   → earn records & materials
   → build/upgrade base, farm, automate tasks with creatures
   → store, customize (spheres/skins), trade, research, compete
```

---

## 6. Feature Requirements

> Each feature lists **FR ids** for traceability. Acceptance criteria (AC) are concrete, testable statements.

### F1 — World & Exploration

- **FR-X1.1 Regions.** The world is divided into data-defined regions (maps, palettes, encounter tables, buildings/towers, base zones, underground entrances).
  - AC: A mod can add an entire region without engine changes.
- **FR-X1.2 Overworld.** Top-down 2D traveling on foot, with tiled terrain of varied types (land, water, lava, snow, air-capable surfaces…).
- **FR-X1.3 Underground.** Each region has an underground sub-world (4th/5th-gen inspired) to encourage exploration: discrete dig spots, mineral/resource nodes, hazards, secret spaces.
  - AC: Alongside walking routes and riding, underground content is discoverable in at least one region by v1.
- **FR-X1.4 Wilderness encounters.** Areas spawn wild creatures from encounter tables (species, levels, terrain/conditions, variant weights).
  - AC: Encounter tables are pure data; a mod can redefine an area's spawns.

### F3 — Creatures & Individuality (DNA)

- **FR-C1.1 DNA.** Every individual has versioned, ID-only DNA: species, growth stage, level, exp, nature, 4 moves, ability, IV set, EV set, variant, bond, records, lineage, ball.
  - AC: The same DNA encodes save, trade, and network states.
- **FR-C1.2 Base stats.** Exact 6 mains: **HP, Speed, Physical Atk, Physical Def, Special Atk, Special Def**.
  - AC: Formulas (damage, stat growth) reference only these six.
- **FR-C1.3 IVs.** Unique per instance; immutable; set at spawn/birth/breeding.
- **FR-C1.4 EVs.** Trainable pool capped by budget (default 200 percent-points; max +100% of base per stat) — allow "2 maxed / 3 at ~67% / 6 at ~34%" or mixed.
  - AC: Respec available only via designated items/features; budget is central in `balance.json`.
- **FR-C1.5 Natures.** A nature modifies two stats (+/−). Purely data.
- **FR-C1.6 Variants.** 8 variants: **normal, albino, melanism, alpha, mutant, runt, giant, hybrid** with distinct rules (see ARCHITECTURE §5.9).
  - AC: Hybrid only via breeding or artificial-creation building process; never wild.
- **FR-C1.7 Growth stages.** Permanent, ordered stages per species (baby→juvenile→adult→…); transitions gated by age/exp and sometimes records/items; aging beats transformation.
- **FR-C1.8 Death.** Creatures can permanently die in defined circumstances (hazards such as holes, certain effects, rare outcomes, story events). Data-controlled; clearly signposted; no cheap permadeath.
  - AC: Death is opt-in per content; the base mod defines v1 death sources.
- **FR-C1.9 Bond.** A per-instance loyalty stat, influenced by taming vs capture, actions, time, and care.
  - AC: Bond feeds friendly-fire odds, ride performance, and base-task output.

### F4 — Taming vs Capturing

- **FR-T1.1 Taming.** Earn trust in the wild (patience/observation/interaction). Tamed creatures level up faster and bond more easily, but starting on the team costs effort.
- **FR-T1.2 Capturing.** Spherical devices ("spheres") capture wild creatures immediately. Captured creatures level slower and bond slower, but join the team at once.
  - AC: Battle potential identical; only growth/bond curves differ (data-driven).

### F5 — Storage, Spheres & Towers

- **FR-S1.1 Spheres.** Containers impose full stasis; emergency-safe release on device damage (data-driven threshold).
- **FR-S1.2 Tower/PC-equivalent.** Towers: pocket-dimension storage, breeding lab, and sphere-skin customization (material fee).
- **FR-S1.3 Ball skins.** Cosmetic customization of sphere appearance, applied at towers; no battle effect except contests.
  - AC: Skins are data items; contests may use them as a judged trait.
- **FR-S1.4 Dex map data.** Towers unlock superficial region data on the player's dex device (map flavor; **no** pins/markers).

### F6 — Research & Dex

- **FR-D1.1 No auto-fill.** Dex data is filled by observing wild creatures performing behaviors with the dex deployed (Pokémon-Snap-style). Variant data is the only automatic entry, recorded at capture/birth.
  - AC: New behaviors = new data chunks; behaviors are data per species.

### F7 — Grid Battles

- **FR-B1.1 Formats.** 1v1 and 2v2 (per battle context). Party size 6; squad selected pre-battle.
- **FR-B1.2 Battlefield.** Rectangular grid, default **12×6**, three zones: home / neutral mid / enemy. Obstacles & terrain per arena (data).
- **FR-B1.3 Positioning.** Moves carry target, range, area (cell/line/burst/zone); repositioning costs turn resources.
- **FR-B1.4 Terrain & hazards.** Holes (fall → knockdown/out), lava/water/fire pools (status/damage), trees/rocks (block movement, cover, line-of-sight).
- **FR-B1.5 Friendly fire & bond.** Area/multi-target effects may hit allies by default. Higher **bond** reduces the per-ally friendly-fire chance, to elimination at high bond.
  - AC: Deterministic outcome for a given seed + modset (required for MP). Base friendly-fire constants in `balance.json`.
- **FR-B1.6 Determinism.** Seeded RNG; no floats in serialized state.

### F8 — Breeding & Evolution-Like System

- **FR-P1.1 Taxonomies.** Species belong to 1–3 taxonomy classes (breeding compatibility + bodyplan + traits).
- **FR-P1.2 Cross breeding.** Rules decide compatible pairs and offspring taxonomies; hybrids/egg moves via breeding or artificial creation.
- **FR-P1.3 Records gate.** Some records gate moves and growth-stage transitions.

### F9 — Riding & Mounts

- **FR-R1.1 Ridable species.** Some creatures are rideable (mounts) for travel.
- **FR-R1.2 Ride types.** Terrain-based: land, water, air, lava, snow, or other terrain.
- **FR-R1.3 Mount gear (key items).** To ride, players capture/tame a ridable creature, then **craft** the matching key item (bridle, mount chair, etc.) specific to creature + ride type.
  - AC: Without the crafted gear, mounting is blocked with a clear message.
- **FR-R1.4 Bond & stats affect riding.** Better bond/stats improve ride performance (speed, stability, terrain tolerance).
  - AC: Ride quality reproducible from DNA-derived values (deterministic).

### F10 — Farming & Bases

- **FR-BA1.1 Base placement.** Bases are sandboxes restricted to **designated base zones** per region — not buildable anywhere.
- **FR-BA1.2 Unlock conditions.** Players must unlock construction tools and obtain **regional permission** before placing a base in that region.
- **FR-BA1.3 Sandbox construction.** Free-form placement of structures/plots/decoration within the zone.
- **FR-BA1.4 Farming.** Crop cultivation on plots: planting, growing phases, watering, harvesting; crops yield materials/items; climate/terrain per region affects crops.
- **FR-BA1.5 Automation.** Stationed creatures automate base tasks (farming, energy generation, resource gathering, crafting assistance, etc.).
  - AC: Output depends on species aptitude + individual stats + **bond**.
- **FR-BA1.6 Persistence.** Base state (plots, buildings, assignments) persists and travels with saves; respecting multiplayer rules later.

### F11 — Records & Creature Achievements

- **FR-RC1.1 Records.** Per-creature history (defeats, formats, finals, streaks…) stored in the device, shown in summary; independent of the player achievement system.
  - AC: HTTP-style JSON events appended to DNA; some gate learnset/growth.

### F12 — Trade, Economy & Multiplayer

- **FR-M1.1 Trading.** Trade creatures = exchange of DNA (spheres/devices), person-to-person.
- **FR-M1.2 Modset handshake.** Matches/rooms pin exact modsets; servers reject mismatches.
- **FR-M1.3 Deterministic sync.** Battle outcomes identical across peers for a given seed+modset.
- **FR-M1.4 Regional/global challenges.** Solo or group objectives across region/world scopes (post-MV beats additive).

### F13 — Modding & Content

- **FR-MD1.1 Authoring.** Any mod = folder or `.zip` (manifest + JSON content + assets), made with a text editor + archiver; no Godot editor required.
- **FR-MD1.2 Mod manager.** In-game enable/disable, dependency & conflict resolution, validation errors presented clearly.
- **FR-MD1.3 Mod store.** Browse, download, and update mods from an `index.json` service; optional curation/signing later.
- **FR-MD1.4 Vetted surface.** Content fails validation with exact path + field diagnostics. Schemas exposed for tooling.
- **FR-MD1.5 AI/CLI tooling.** Schema lint, content tester, and zip packager run headless so humans *and* AI can produce content.

### F14 — Cross-Game Creature Universe

- **FR-CG1.** DNA is the portable identity across franchise titles; history travels with the creature; return trips unlock features.

---

## 7. Economy & Balance Framework

- Single tunable hub: `balance.json` (EV budget, XP curves, catch formula, damage constants, friendly-fire base odds, ride quality curve, base output rates, crop timers, material costs).
- Materials drive: sphere skins, mount gear, construction, farming upgrades, tower services.
- No pay-to-win; monetization out of scope for this doc.

## 8. Non-Functional Requirements

| # | Requirement | Target |
|---|---|---|
| NFR-1 | Determinism | Identical battle outcomes for same seed + modset |
| NFR-2 | Mod safety | Mods execute zero code; validated against schemas at load |
| NFR-3 | Save integrity | Versioned DNA; migrations supported; no float state |
| NFR-4 | Accessibility | Key prompts UI-accessible; death risks clearly signposted |
| NFR-5 | Performance | Pixel-art 2D target: smooth on mid hardware; Android/Web friendly |
| NFR-6 | Platform limits | Web filesystem limits for zip/cache handled |

## 9. Success Metrics

- Mods authored by outsiders without the editor (number + self-reported ease).
- Variant/breeding meta participation (hybrids bred, records earned).
- Exploration depth signal: underground visits, riding usage, dex completion via research.
- Deterministic-combat confidence for MP (no desyncs in seeded battles).

## 10. Milestone Scope (echo of ARCHITECTURE §13)

- **M0** Foundations & mod loading · **M1** Battle core · **M2** Authoring pipeline · **M3** World + taming/capturing + riding · **M4** Progression: growth, records, research, breeding, **bases/farming** + **underground** · **M5** Mod manager + store · **M6** MP-forward.

## 11. Risks & Open Questions

- **Death tuning** — permadeath vs fairness; needs clear UX protection.
- **Friendly fire UX** — must communicate odds; potentially contentious in competitive play; constants tunable.
- **Base placement rules** — balancing sandbox freedom with region integrity.
- **Underground scope** — "in some way" per request; v1 may ship a focused subset (dig sites + secret spaces + resources).
- **Mod store trust** — signing/curation is post-v1.

## 12. Glossary

- **DNA** — versioned ID-only encoding of an individual creature (species→ball).
- **Variant** — one of 8 appearance/species-level forms (normal is the first).
- **Taxonomy** — breeding/bodyplan class (max 3 per species).
- **Bond** — per-instance loyalty stat feeding friendly fire, riding, base labor.
- **Records** — per-creature history gates (moves, growth).
- **Sphere** — storage device; **Tower** — storage/lab/customization hub.
- **Base zone** — designated buildable area requiring permission + tools.
- **Underground** — exploration sub-world per region.

---

*Product decisions are tracked in GitHub Discussions; this PRD is updated as the live spec.*