# Science Shorts Engine

Code-rendered vertical science shorts (1080×1920 @ 30 fps) in the style of viral
"body-fact journey" videos: a persistent progress meter, escalating facts, giant
stat headlines, karaoke captions, procedural ambience, loop-close narration.

Built from a deconstruction of a viral Everest short (hook → ALTITUDE counter →
escalating body facts → dark stat → loop close, 186 words @ 153 wpm) and rebuilt
as a fully local, deterministic, zero-cost pipeline.

## Videos in this release

| Video | Meter | Length |
|---|---|---|
| **What falling to the bottom of the ocean does to your body** (Mariana Trench) | DEPTH 0 → 10,935 M | 78 s |
| **Falling into a black hole** (Sagittarius A*) | DISTANCE TO HORIZON 42,000,000 → 0 KM | 66 s |
| **What the first years of life do to a child's brain** (education/pedagogy) | CHILD'S AGE 0 → 25 YRS | 77 s |

Download them from the [Releases page](../../releases).

## Pipeline (all local, free, deterministic)

```
Edge-TTS narration  →  faster-whisper word alignment
  (timings mapped back onto the script text via difflib, so ASR
   mis-hearings never corrupt captions)
→  Playwright (Edge) frame-stepping of a deterministic Canvas 2D renderer
→  ffmpeg image2pipe H.264 + numpy-synthesized ambience bed
   (abyss rumble+sonar / space drone / warm nurture pad)
→  loudness-normalized AAC mix (−14 LUFS)
```

A ~75 s video renders in ~6–8 minutes on a CPU-only laptop.

## Repo layout

```
engine/
  render.html   deterministic 1080×1920 Canvas renderer (scene painters + overlays)
  render.py     Playwright frame-stepper → ffmpeg pipe (also: stills mode)
  tts.py        Edge-TTS + whisper word alignment
  audio.py      procedural ambience + narration/bed mix
  build.py      orchestrator (spec.json → out/<name>.mp4)
videos/
  mariana/spec.json
  blackhole/spec.json
  brain/spec.json
```

## Make your own

1. Copy a spec: `cp -r videos/mariana videos/mytopic` and edit `spec.json` —
   the script, the meter (a number that only moves one way), scenes, and
   stat headlines anchored to spoken words.
2. Build: `python engine/build.py videos/mytopic/spec.json`
3. Preview stills: `python engine/render.py work/mytopic/render_spec.json "qa/x_%d.png" "3,20,40,60"`

Scene painters available: `water` (light rays + marine snow), `walls` (trench
walls), `abyss` (darkness + bio-flickers), `space` (starfield + nebulas),
`blackhole` (lensed accretion disk), `warp` (star streaks), `pulse` (heartbeat
tint), `neural` (growing/pruning brain network, serve-and-return mode).

The full formula + topic queue + posting strategy: [`SCIENCE-SHORTS-PLAYBOOK.md`](SCIENCE-SHORTS-PLAYBOOK.md).

## Branding

`meta.brand` in each spec holds the top-left logo block — change `AXIOM` to
your channel name. Fonts are vendored Oswald + system Georgia (no CDN at render time).

## Requirements

- Python 3.12+: `pip install playwright edge-tts faster-whisper numpy`
- `ffmpeg` on PATH, Edge/Chromium for Playwright (`playwright install msedge` or use channel default)

MIT licensed. Educational facts are sourced in the playbook's fact ledger —
verify before re-recording.
