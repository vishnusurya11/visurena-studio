# Ten narrated book scenes built in Blender by an AI agent: five in 3D from generated meshes, five in 2D from generated layers

*One night, one RTX 4090, no paid services. November 8 to 9, 2026.*

## The question

Can an AI agent drive Blender well enough to stage, light, shoot and render a short narrated scene, when every
asset in the scene is itself generated? And which is the better route for book adaptations: a real 3D set built
from generated meshes, or a 2D multiplane shot built from generated drawings?

## What was built

Ten scenes of 46 to 48 seconds each, with a narrator and a music bed, from ten modern novels (a private test:
written in our own words, never published). Each scene is seven shots cut to the measured length of its narration.

| Route | Scenes | Looks |
|---|---|---|
| 3D: generated meshes staged in Blender | a candlelit attic, a warship passing a gas giant, an airlock tunnel, a desert at dawn, a neon racetrack | anime cel, path-traced realistic, game cinematic |
| 2D: generated drawings split into layers and stacked in Blender | a rain-soaked street, an examination hall, a gothic corridor, a tavern table, a gorge parapet | each scene in its own anime style |

Nine of the ten scenes were built a second or third time after the first version was watched. Each strip shows
one frame every five seconds of the latest version.

**3D route**

![A candlelit attic, anime cel look: one frame every five seconds](images/3d_attic.jpg)

![A warship passing a gas giant, path-traced: one frame every five seconds](images/3d_warship.jpg)

![An airlock tunnel, game look: one frame every five seconds](images/3d_airlock.jpg)

![A desert at dawn, anime cel look: one frame every five seconds](images/3d_desert.jpg)

![A neon racetrack, game look: one frame every five seconds](images/3d_racetrack.jpg)

**2D route**

![A rain-soaked street, ink drawing: one frame every five seconds](images/2d_street.jpg)

![An examination hall: one frame every five seconds](images/2d_hall.jpg)

![A gothic corridor by lamplight: one frame every five seconds](images/2d_corridor.jpg)

![A tavern table: one frame every five seconds](images/2d_tavern.jpg)

![A gorge parapet in a storm: one frame every five seconds](images/2d_parapet.jpg)

## How a 3D scene is made

1. **Words to pictures.** For each prop and character, one picture: a single object on a white ground, seen from
   three-quarters, already in the pose the scene needs (Qwen-Image 2.1).
2. **Pictures to meshes.** Each picture becomes a textured mesh (Pixal3D on the TRELLIS.2 backbone, running inside
   ComfyUI). A seated figure with its chair and cane came back complete from every side, back included.
3. **Words to a room.** A 360-degree picture of the empty place (Qwen-Image with a panorama add-on) is projected
   onto a room-sized box in Blender from eye height. The painting then sits at real distances, so a moving camera
   gets real parallax. Exteriors use the panorama as the sky and a built ground.
4. **Staging through the Blender MCP.** The agent imports the meshes, scales each to a real height, reads a
   top-down render to find which way each one faces, places them, sets lamps, and gives every shot its own camera
   bound to the timeline. It looks at stills and corrects itself, three rounds at most.
5. **A look.** The same staged scene renders as anime (stepped toon light plus an ink outline), as path-traced
   realism, or as a game cinematic (ray-traced real-time with fog).
6. **Render on the GPU**, then narration, music, loudness, upscale.

Characters are statues: nothing is rigged. Motion comes from the camera, flickering light and vehicles on
straight paths. That limit shaped which scenes went to 3D.

## How a 2D scene is made

1. **One drawing per shot** in the scene's anime style, with one fixed description for every recurring person and
   prop so they stay the same from shot to shot.
2. **Split into layers.** The subject is cut out with a matting model; the background behind it is repainted by an
   image-edit model and blended only inside the hole. (A dedicated layer-decomposition model was tried first: it
   took six minutes per picture and returned a usable split for two shots of seven, so it was retired.)
3. **Multiplane in Blender.** Layers become unlit planes at increasing depth, scaled so the first frame matches the
   drawing exactly. A slow camera move gives parallax; rain, dust and speed lines are drawn as Grease Pencil
   strokes; a second expression plate can fade in mid-shot (a face going from fear to resolve).
4. **Render on the GPU**, then the same audio chain.

## Measured on one RTX 4090 (1280x720, 24 fps)

| Step | Time |
|---|---|
| Mesh from one picture (Pixal3D, 150k faces, PBR textures) | 331 s for the first, 140 to 200 s after |
| 360 panorama, 2048x1024, 40 steps | about 5 min |
| Staging a scene through the MCP (import, place, light, cameras, three rounds of stills) | 8 to 17 min of agent time |
| Render, anime cel or game look (EEVEE) | 0.21 to 0.26 s per frame |
| Render, path-traced (Cycles OptiX, 48 samples, denoised) | 1.5 s per frame; 0.26 s once the scene is kept on the card between frames |
| A whole 48 s scene, any look | about 4 to 5 min of render |
| 2D multiplane scene, 1126 frames | 3.4 min of render |
| Second version of a 3D scene (re-stage two shots, re-render, re-master) | about 15 min |
| Second version of a 2D scene (redraw seven drawings, re-split, re-render, re-master) | about 20 to 25 min |

## What went wrong, and the rule each failure left behind

- **Imported meshes ignore the rotation you set.** A glTF import leaves objects in quaternion mode; set the
  rotation mode first. Nothing turned for three rounds until a top-down render showed it.
- **Image-to-3D bakes the picture's camera tilt into the mesh.** A table top came back sloped. Rotating the mesh
  until its broad upward surface is level fixes it.
- **A toon ramp reads absolute light.** Lamps that suit the path tracer leave a face in the shadow band, lit only
  along its facets, which draws bright cracks. Smooth the normals and raise the lamps for the cel look; outdoors
  the ramp's step has to move as well.
- **A workflow's hidden upscale stage ran the machine out of memory.** The panorama template loaded a second large
  model on top of the first and the server died. Save the decode directly and enlarge it cheaply.
- **Generated models pile up in RAM.** Three model families in a row left 0.3 GB of commit memory. Unload on every
  change of family, one heavy job at a time, first come first served.
- **A gate with a guessed threshold destroyed good work.** An uncalibrated frame gate "cured" all seven 2D shots by
  flattening them. Thresholds come from measured good cases, and a cure must be reversible.
- **A style card overrides the script.** A card painted a violet sunset where the script said storm, and an open
  sky where it said indoors. Stating the weather once was not enough: the storm held only when the prompt opened
  with it and closed by ruling out the sunset's colours. Place, weather and time of day belong in the fixed
  description that every shot shares.
- **A glass pane washed out a whole shot.** Its default reflectivity mirrored the bright room. It was found by
  hiding objects one at a time, not by reasoning about the grade.
- **A pass claim was made on half the evidence.** One scene was reported as passing after two of its four gate
  results were read; its motion gate had failed on a nearly frozen shot. Every finishing run now prints one line
  per gate, and a pass is stated by naming the gates.
- **A dedicated layer-split model was the wrong tool.** Slow and unreliable on hatched drawings; a matte plus an
  edit is faster and holds.

## What this suggests

- For hard-surface subjects (ships, vehicles, props, sets) the 3D route already produces shots that hold up, at
  minutes per scene, and one staged scene yields any look.
- For faces, mood and weather, the 2D route keeps the drawing's quality and costs less; its motion vocabulary is
  small (push, pan, parallax, plate swaps).
- The agent's real work is staging by looking: a plan view and a contact sheet per round did more than any metric.

## Reusable pieces

- A Blender-side library: import and fit a mesh, level it, panorama room, per-shot cameras, three looks.
- A layered multiplane builder with Grease Pencil effects and expression plates.
- A first-come-first-served GPU turn lock that unloads models between families.
- A client for the official Blender MCP server that scripts can call.
