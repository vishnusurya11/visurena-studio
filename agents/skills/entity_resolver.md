# Skill: entity resolver — canonical characters & locations (analysis 03)

You receive every character reference and every location reference that extraction
found in one novel, each with the chapters it appeared in and a sample scene summary.
Merge the surface forms into canonical entities. You never re-read the book — you work
only on this list.

## Characters

Group the surface forms that refer to the SAME person into one entity:
- `id`: snake_case stable id (`holmes`, `watson`, `jefferson_hope`, `lucy_ferrier`)
- `name`: the fullest proper name the text uses
- `aliases`: every surface form that maps here — including nominal descriptions
  ("the detective", "my companion") and, for a first-person narrator, "I"/"me"
- `role`: `protagonist` | `major` | `minor` | `group` | `unnamed`
- `first_chapter`: earliest chapter it appears in

Rules:
- Merge only what the evidence supports. If the narrator is Watson, "I" is Watson.
- **Two different proper names are two different people.** Murray is not Williams.
  Merge named figures ONLY where the text states the identity — and then say which
  reveal states it, in `merged_because`.
- **Masked identities**: if the text reveals that one figure IS another (the cabman is
  Jefferson Hope), merge them and record BOTH names in aliases.
- Do NOT merge two different people who share a description ("the constable" x2 may be
  different constables) — leave the generic form as its own `unnamed` entity.
- **Same word, different world.** A common noun keeps the sense of the passage it
  appears in. Watson's "many other officers" are army officers in Afghanistan and have
  nothing to do with the London police; "the men" on a Utah trail are not the Baker
  Street irregulars. Before aliasing a role noun to a standing group, check that the
  group is actually present in that part of the book. When two passages use the same
  word for different people, the word belongs to NEITHER canonical entity.
- Drop pure generics that are not characters ("a medical board", "a paternal
  government", "a great train of wounded sufferers").
- Groups ("the Mormons", "the Four", "the police") are `role: group` entities — keep.
- **A one-word alias must be a name.** "Young" earns its place as Brigham Young's alias;
  "men", "women", "he", "her" do not belong in any alias list. Bare pronouns and bare
  plurals refer by context, and you are working without the context — you cannot resolve
  them, so leave them out rather than guess.

## Locations

Group surface forms into canonical places and GIVE EACH REAL-WORLD COORDINATES:
- `id`, `name` (canonical), `aliases`
- `region`: `london` | `utah` | `pursuit` | `other`
- `lat`, `lon`: decimal degrees. Use real coordinates for real places. For places
  the author invented but anchored to a real street/district (3 Lauriston Gardens
  "off the Brixton Road"), use the anchor's coordinates and set `approximate: true`.
- `approximate`: bool — true when the address is fictional or vaguely stated.

Known anchors for A Study in Scarlet (use these when they match):
221B Baker Street 51.5238,-0.1586 · Criterion Bar/Piccadilly 51.5101,-0.1340 ·
St Bartholomew's Hospital 51.5175,-0.1000 · Lauriston Gardens/Brixton Rd ≈51.470,-0.114 ·
Audley Court/Kennington ≈51.484,-0.109 · Torquay Terrace/Camberwell ≈51.474,-0.092 ·
Houndsditch ≈51.515,-0.078 · Halliday's Hotel/Little George St ≈51.500,-0.127 ·
Scotland Yard 51.5062,-0.1259 · Euston Station 51.5282,-0.1337 ·
Great Alkali Plain/Salt Lake Desert ≈40.8,-113.5 · Salt Lake City 40.7608,-111.8910 ·
Ferrier farm/Wasatch foothills ≈40.6,-111.6 · Eagle Cañon ≈40.5,-111.5 ·
Carson City 39.16,-119.77 · Cleveland 41.50,-81.69 · St Petersburg 59.93,30.34 ·
Copenhagen 55.68,12.57 · Afghanistan/Maiwand ≈32.0,65.0 · Peshawar 34.01,71.58 ·
Portsmouth 50.80,-1.09 · Netley 50.87,-1.36

Rules:
- Merge vague forms into the specific place when they clearly refer to it ("our
  lodgings", "the sitting-room" → 221B Baker Street). But a room name that any house
  could have ("the sitting-room", "the bedroom") is a WEAK alias — attach it only to the
  building the book overwhelmingly means by it, never to two.
- A span listing several places ("India, Afghanistan, Peshawar, England, London") is a
  route, not a place. **Give each place its own canonical entity**; do not bury the
  others in one entity's aliases. A later step walks the route leg by leg, and it can
  only do that if the legs exist as places.
- Never invent a coordinate for a place you cannot place: use `region: other` with the
  best guess and `approximate: true`.

---

## Interiors need their own entries, or every scene inside them is mis-placed

An audit of three books by independent judges found the same gap five times: the
registry held a town, and the scene happened in a room the registry had no entry for.

> `ingolstadt` — the scene is in **the vaults and charnel-houses**
> `orkney_island` — the scene is in **Victor's laboratory**
> `geneva` — the scene is in **a barn**
> `ireland_harbour_town` — the scene is in **a prison**

Each of those was then filed under the town, which is a place no camera can stand in.
**A settlement entry does not cover the interiors inside it.**

So: **when the text names a room, a building, or an enclosed place, it earns its own
canonical location** — even if it also sits inside a town you have already created, and
even if it appears once. A location used by a single scene is not clutter; a scene filed
under a county is a scene nobody can shoot or place on a map.

Give the interior the containing settlement's coordinates. Being unable to geocode a barn
is not a reason to file the scene under the county.

**Vehicles are locations too.** A cab, a carriage, a ship's cabin, a railway compartment
— a camera can be inside one, characters spend whole scenes there, and *"in a cab
returning to Baker Street"* came back from the audit as a place the registry lacked.

**The names to be most careful with are the ones that sound like locations and are not:**
a country, a county, a state, an island, a region. Those belong in the registry only when
a scene genuinely plays ACROSS them — a voyage, a crossing, a pursuit over open country —
never as the home for a scene that happens in one room.
