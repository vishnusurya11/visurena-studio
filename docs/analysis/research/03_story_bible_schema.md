# Research 3 — Story-bible output schema (Aug 2026)

*Wave-1 subagent report, 2026-08-22. Consumer legend: 🎧 audiobook, 🎬 shorts, 🎵 songs, 📖 derived novels.*

## Part 1: What each source system contains

### Sudowrite Story Bible
Layered: Braindump → Genre → Style → Synopsis → Characters → Worldbuilding → Outline → Scenes. Character card default traits: **Pronouns, Groups, Other Names, Personality, Background, Physical Description, Dialogue Style** + custom. Two details to steal: "Other Names" exists for alias resolution; "Groups" for machine-resolvable faction membership. Principle: "AI depends on specificity."
(https://docs.sudowrite.com/using-sudowrite/1ow1qkGqof9rtcyGnrWUBS/what-is-story-bible/jmWepHcQdJetNrE991fjJC)

### Worldbuilding tools
- **World Anvil** (~25 templates): Character, Settlement, Geography, Building, Organization, Ethnicity, Tradition, Myth, Religion, Species, Item, Spell, Technology, Title/Rank, Natural Law, Plot… Character template tabs: Generic (eye color, gender, current location, birth/death), Naming, **Physical** (looks+clothes+equipment), Mental, Personal (motivations, virtues/flaws), Social, Divine. Creation method: role → motivation → obstacle.
- **Campfire** — 17 modules; **Timeline**, **Arcs**, **Relationships** are first-class objects, not fields.
- **LegendKeeper** — no fixed taxonomy; user-defined typed templates + auto-linking wiki. Lesson: keep schema extensible.

### Fandom wiki conventions (decades of community consensus)
- **Coppermind** character article: Infobox → Intro → **Appearance and Personality** → **Attributes and Abilities** → **History** (longest, dated subsections) → **Relationships** → Trivia. Infobox: ethnicity, birthplace, residence, world, family, born/died, titles, **aliases**, abilities, profession, religion, groups, species, era, **introduced** (first book). Settlement articles: Geography → Landmarks → History → Culture → Politics → Notable Citizens.
- **A Wiki of Ice and Fire**: Jon Snow — Appearance and Character → History → **Recent Events per book** → Quotes by/about → Family. Winterfell — Household, Layout, History, and "**Chapters that take place in Winterfell**" (location→chapter index).
- **The big wiki lesson: per-book/per-chapter provenance of every fact, and bidirectional entity↔chapter indexes, are the load-bearing structure.**

### TV/film show bible (what it adds that wikis don't)
Logline → series overview → **The World and its Rules** (explicit: how the magic works, what it costs, what it *cannot* do) → **Tone & Style page** (adjectives + comparable works) → character breakdowns (casting-style physical description) → arcs → episode guide. Animation bibles: **model sheets** (turnarounds, expressions, costume, color schemes) + **visual style guide** (palette, framing, line/color language) — exactly what the shorts Art Director stage needs as input.

### Adaptation practice (what screenwriters extract first)
(1) **Beat sheet** — chronological significant events *that can be shown visually*; (2) **causal chain** — the 5-10 load-bearing beats; (3) most visual, emotionally resonant **set-piece scenes**; (4) scene-by-scene **step outline** (action + emotional point per scene); (5) three-act mapping; (6) **interiority flags** — internal-monologue beats needing external/visual form. Implies each scene needs a *visual filmability score* and an *emotional function*.

### AI image-gen character consistency practice
Locked visual attribute table: age, gender presentation, build/height, face shape, skin tone, eyes{color,shape}, hair{length,color,texture,style}, distinguishing marks, signature outfit{colors,materials}, signature prop, expression baseline, art style. Rules: **50-100 word description, copied verbatim never paraphrased**, fixed character-block + variable scene-block prompt structure, never improvise an attribute.

### Audiobook narrator prep
Character list with **accent/voice notes**, **pronunciation guide** (invented names, places, foreign phrases), character profiles; narrators mark dialogue attribution and emotional register per scene.

## Part 2: Recommended schema

Cross-cutting principles:
1. **Every field carries provenance** — `first_appearance` + per-fact chapter citations. Enables spoiler-safe slicing and "state of the character as of chapter N."
2. **Canonical name + alias table per entity.**
3. **Separate extracted (cited) from studio-decided (inferred/invented, marked)** — image-gen-grade visual detail always exceeds what the novel states; mark the delta.
4. **Time-varying attributes get versions** (appearance/age/wardrobe per era) — wikis use dated History subsections; image-gen needs discrete locked variants.

### (a) Character
| Field | Consumers |
|---|---|
| `id`, `canonical_name`, `aliases/nicknames/titles/epithets` | all |
| `pronouns`, `gender_presentation` | 🎧🎬📖 |
| `role_in_story`, `archetype` | 🎬🎵📖 |
| `importance_tier` + `chapter_appearances[]` | 🎧🎬📖 |
| `species/ethnicity/culture/nationality` | 🎧(accent)🎬(look)📖 |
| `allegiances/groups/factions` | 🎬(costume/heraldry)📖 |
| **`physical` block — locked visual attributes** (age_range per era, height/build, skin_tone, face_shape, eyes, hair, facial_hair, marks, posture/gait, signature_wardrobe per era, signature_props, `stated_vs_inferred` per attribute, compiled **50-100 word verbatim prompt block**) | 🎬 critical, 📖 |
| `personality` (temperament, virtues/flaws, quirks) | 🎧🎵📖 |
| `motivation`, `internal_conflict`, `wound/backstory` | 🎵🎬📖 |
| `character_arc` (start → end, turning-point chapters) | 🎵🎬📖 |
| **`voice` block** (dialogue_style, register, accent, catchphrases, quirks, vocal quality) | 🎧 critical, 📖 |
| `name_pronunciation` (phonetic) | 🎧 critical |
| `relationships[]` {other_id, type, dynamic, evolution, arc effect} | all |
| `abilities/skills/powers` | 🎬📖 |
| `history` (dated biography) | 📖 |
| `key_quotes[]` (by and about, cited) | 🎧🎵🎬 |

### (b) Location
| Field | Consumers |
|---|---|
| `id`, `canonical_name`, `aliases`, `type` | all |
| `parent_location` / containment hierarchy | 🎬📖 |
| `geography` (setting, topography, climate) | 🎬📖 |
| **`visual` block** (architecture, materials, palette, scale, lighting character, condition, era, sensory signature, mood, stated_vs_inferred, compiled prompt block) | 🎬 critical, 🎵📖 |
| `landmarks/sub-locations[]` | 🎬📖 |
| `inhabitants`, `notable_residents[]` | 🎧🎬📖 |
| `government/ruler/religion`, `culture` | 📖🎬 |
| `history` (dated) | 📖 |
| **`scenes_set_here[]`** (chapter/scene index) | 🎬 critical, 🎧 |
| `narrative_significance` (emotional meaning) | 🎵🎬📖 |

### (c) World / Universe
| Field | Consumers |
|---|---|
| `setting_overview` (era, tech level, analog, scope) | all |
| **`rules_of_the_world[]`** (statement + costs/limits + cannot-do + exceptions) | 🎬📖 critical |
| `factions[]` {purpose, members, iconography, conflicts} | 🎬📖 |
| `cultures[]`, `religions[]`, `languages[]` (+ naming/pronunciation patterns) | 🎧🎬📖 |
| `species/creatures[]` (with visual blocks) | 🎬📖 |
| `items/artifacts[]` (props, visual descriptions) | 🎬📖 |
| `myths/lore` (pre-story history) | 🎵📖 |
| **`timeline[]`** (in-world dates ↔ chapter refs, flashback mapping) | 🎧🎬📖 critical |
| `glossary/pronunciation_guide[]` | 🎧 critical, 📖 |
| `maps/spatial_relations` (travel times, adjacency) | 📖🎬 |

### (d) Chapter / Scene (scene = atomic unit)
| Field | Consumers |
|---|---|
| `chapter_no`, `title`, `word_count`, `summary` | all |
| `pov_character`, `narration_tense` | 🎧 critical, 📖 |
| `timeline_position` (in-world date; flashback?) | 📖🎬 |
| Per scene: `location_id`, `time_of_day`, `weather`, `characters_present[]`, `action_summary`, `emotional_function`, `conflict/stakes`, `outcome/state_change` | 🎬🎧📖 |
| `dialogue_map` (who speaks; notable exchanges) | 🎧 critical |
| `is_load_bearing` + `beat_label` | 🎬🎵📖 |
| **`visual_potential_score` + `set_piece_flag`** | 🎬 critical — how the Story Scout picks scenes |
| `interiority_notes` | 🎬🎵 |
| `mood/tone tags`, `sensory highlights` | 🎧🎵🎬 |
| `first_introductions[]` (entities debuting here) | all (spoiler gating) |
| `key_quotes[]` | 🎵🎬 |

### (e) Book-level metadata
| Field | Consumers |
|---|---|
| `title, author, series_position, PD status` | all |
| `logline` | 🎬🎵 |
| `synopsis` (incl. ending, emotional arc, stakes) | all |
| `genre` + `comparable_works` | 🎬🎵📖 |
| **`tone_and_style`** (adjectives, prose voice, pacing, rating) | all |
| `themes[]` + `motifs/symbols[]` (lantern, winter, blood…) | 🎵 critical, 🎬📖 |
| **`pov_structure`** (person, single/multi, POV chapter counts, reliability) | 🎧 critical, 📖 |
| `structure` (act boundaries, beat sheet, causal chain) | 🎬📖 |
| `timeline_span` + chronology type (linear/nonlinear) | 🎧📖 |
| `arcs[]` (character + plot, book/series span) | 🎵📖🎬 |
| **`visual_style_guide`** (studio-decided: palette, lighting, framing, art key) | 🎬 critical |
| `language_notes` (period diction, profanity, dialect density) | 🎧📖 |

**The three fields no existing writer's tool has, that this pipeline needs most:**
1. Locked verbatim visual prompt block with stated-vs-inferred flags (AI-art practice + animation model sheets)
2. Per-scene visual_potential / set-piece scoring (adaptation triage)
3. Entity↔chapter bidirectional index with first-appearance provenance (wiki conventions)

Sources: Sudowrite docs · worldanvil.com/learn · Campfire · Coppermind Help:Article_structure · AWOIAF (Jon Snow, Winterfell, infobox docs) · StudioBinder show-bible guides · adaptation guides (StudioBinder, ScriptReaderPro) · AI-consistency guides (toonystory, smartaiedits, kling.ai) · audiobook prep (Pozotron, Narrator's Roadmap)
