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
- **Masked identities**: if the text reveals that one figure IS another (the cabman is
  Jefferson Hope), merge them and record BOTH names in aliases.
- Do NOT merge two different people who share a description ("the constable" x2 may be
  different constables) — leave the generic form as its own `unnamed` entity.
- Drop pure generics that are not characters ("a medical board", "a paternal
  government", "a great train of wounded sufferers").
- Groups ("the Mormons", "the Four", "the police") are `role: group` entities — keep.

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
  lodgings", "the sitting-room" → 221B Baker Street).
- A scene listing several places ("India, Afghanistan, Peshawar, England, London") is a
  SUMMARY sweep — canonicalize it to the single most important one and note the rest
  in aliases.
- Never invent a coordinate for a place you cannot place: use `region: other` with the
  best guess and `approximate: true`.
