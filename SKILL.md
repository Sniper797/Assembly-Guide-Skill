---
name: building-3d-assembly-guides
description: Use when the user asks how to assemble or put together a device, printed parts or a CAD model — «طريقة التركيب», «كيف أركّب», «اشرح التركيب»، «دليل تركيب», assembly instructions, build steps — or asks for an HTML/page explaining assembly, especially when Fusion, STEP or STL files of the parts exist, or when an earlier assembly page was «مو واضح».
---

# Building 3D assembly guides

## Overview

The answer to "how do I assemble it?" is **one HTML page: numbered step cards on one side, a
sticky three.js bench on the other that shows the device after each step**, driven by scrolling.
The part you fit now is orange and flies in along its real insertion path. Every part comes from
the real CAD; every number in the text is measured from it. This format was chosen over 2D
drawings, which were not clear enough.

**Core principle:** writing the steps is a fit check. Steps that read fine can be impossible —
a clamp nobody can reach, a pivot that only goes in by bending a printed ear. Check each step
against the geometry before you write it.

Worked example (small electronics box, 8 steps): `example/template.html` + `example/build_parts.py`.
Every part there is drawn in code, so it runs without CAD: `python example/build_parts.py`, then
`python build_html.py example example-box`, then open `example/standalone.html` from a local server.

## Pipeline

| File | Job |
|---|---|
| `meshes/` | Every body in ONE assembly frame, mm. Fusion: `fusion_export_meshes.py` ([FusionAgent](https://github.com/Sniper797/Fusion-Agent), read-only, `--args {"root": "<component>", "dir": "..."}`), also writes round holes + parameters. Otherwise load the print STLs and place them. |
| `build_parts.py` | Groups bodies into viewer parts; draws bought hardware (screws, nuts, inserts, cables, links) from measured numbers; writes `parts.json` (int16 at 0.01 mm, base64). |
| `template.html` | Page + viewer, `__PARTS_JSON__` placeholder. Copy the example, keep its engine, rewrite KIND/STEPS and the cards. |
| `build_html.py` | template + parts.json → artifact page (no doctype) + `standalone.html`. |

## Writing the steps

1. **Start where the user is.** If a photo/video shows a half-built unit, say «إن كان … فابدأ من الخطوة N» in the header.
2. **Answer "what is all this?" first.** Printed boxes with many holes confuse; give tour steps (front, below, top) that only show the part with a tag on every opening.
3. **One action per card**: what to do, a green «الفحص» (how they know it worked), an amber note only for a real trap, a grey «لماذا».
4. **Step data** (`STEPS` in the template): `show`, `fresh` (orange), `path` (offsets the fresh part travels — its real insertion direction), `delay`, `cam [target, dir, dist]`, `tags [[part, point, text]]`, `clip: true` to cut printed parts at x = 0 for internal fits.
5. **A part has the shape it has at that step.** A cable before the box exists hangs loose (`cable0`); swap to the routed one when the box goes on. Never show a part in a place it can't be yet.
6. Closing sections: why any non-obvious rule exists, and «ما لم يُجرَّب بعد» listing every assumption.

## Checks before publishing

| Check | How |
|---|---|
| Every screw/insert/clamp reachable by a straight tool | `python reach_check.py meshes/*.json --at x,y,z` — 0 escaping directions = unreachable. Say which side is open (e.g. "+Y open → L-key from the front"). |
| Every `path` is collision-free | The fresh part's offset must slide past what's already installed (check clearances along the move, e.g. ring in tunnel 1.5 mm). |
| Order doesn't need bending or a part that's already blocked | Walk the steps against the model; if a step fails, change the order or flag a design fix. |
| Page renders, no console errors, desktop + 375 px | Static server in `.claude/launch.json`; if the Browser pane is hidden, `resize_window` to a size first; click `#stepN` cards and wait ~3 s (the camera tween runs slowly when hidden). |

Found a design flaw while checking? Put the workaround in the step, explain it in an amber note, list it under «ما لم يُجرَّب», and tell the user — don't silently redesign.

## Common mistakes

- Overwriting an old guide with a new URL: publish with the old artifact `url`.
- Exporting from Fusion with `setSurfaceTolerance(0.01)` → Fusion hung > 20 min. Use `HighQualityTriangleMesh`.
- Coordinates beyond ±327 mm overflow int16: shift or scale before quantising.
- Tags on parts hidden by the cut: the template hides tags with x > 0 on clipped parts — put clip-step tags at x ≤ 0.
- `parts.json` must not contain `</` (it sits inside a `<script>`).
- `fusion_export_meshes.py` is checked only on a root whose children share its frame (one 27-body assembly, ≤ 0.006 mm); with moved children, compare one body against Fusion's measure tool.
