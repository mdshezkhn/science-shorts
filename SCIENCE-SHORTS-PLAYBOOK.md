# Science Shorts — Video Formula & Production Engine

Deconstructed from the reference video (LIFE / "What Everest does to your body", 720×1200, 74s)
and rebuilt as a fully local, code-rendered production pipeline.

---

## 1. Anatomy of the reference (why it works)

| Device | What the reference does | Why it hooks |
|---|---|---|
| **Visceral hook (0–6s)** | "At the top of Mount Everest, your body is slowly dying with every breath you take." | Second-person + mortal stakes → instant curiosity gap |
| **Progress meter** | ALTITUDE counter ticks 5,605 → 8,849 M for the whole video | An *open loop* you can see — viewers stay to watch the number complete |
| **Escalation ladder** | One body-fact every 4–6 s, each scarier than the last (blood thickens → can't digest → muscle-eating → death zone → drowning on dry land → brain swelling) | Retention curve: something *changes* constantly |
| **Stat headlines** | 2–3× per video: letter-spaced eyebrow + giant condensed text ("YOUR BLOOD GETS / THICK AND STICKY") | Screenshot-able, shareable, re-hooks muted viewers |
| **Karaoke captions** | Serif captions appear phrase-by-phrase with the voice | 85% of Shorts views are muted — captions carry the video |
| **Dark stat crescendo** | "Over 300 people have died… many of them are still up there." | Emotional peak right before the end = comments/shares |
| **Loop close** | Last line repeats the first line ("…your body is slowly dying with every breath you take") | Seamless loop → rewatch rate → algorithm boost |

Narration measured: **186 words / 73 s ≈ 153 wpm**, calm deep male voice, start at 0.6 s.

## 2. The formula (fill in the blanks)

```
[0–6s]    HOOK: shocking second-person claim + show the meter starting
[6–15s]   FACT 1 at the "start" of the journey (mild)
[15–55s]  FACTS 2–6: escalating, keyed to the meter; put ONE counterintuitive
          twist in the middle ("You wouldn't explode")
[55–65s]  LANDMARK + dark stat ("8 tons per square inch")
[65–73s]  LOOP CLOSE: "Because…" + rephrase of the opening line
```

Script rules: 175–190 words. Short sentences. Numbers written out how they're
pronounced ("eight thousand three hundred"). One twist. One dark stat. Loop echo.

**Meter concept** = the spine. Pick a number that can only go one direction:
altitude ↑, depth ↓, distance-to-event-horizon ↓, time-since-big-bang ↑,
temperature ↓, speed ↑, years-back-in-time ↑…

## 3. Engine — how to produce a new video

```
science-shorts/
  engine/            render.html (canvas renderer) · render.py · tts.py · audio.py · build.py
  videos/<name>/spec.json     <- everything about one video lives here
  out/<name>.mp4              <- finished upload-ready file
```

Produce: `C:/Python314/python.exe engine/build.py videos/<name>/spec.json`
Preview stills: `C:/Python314/python.exe engine/render.py work/<name>/render_spec.json "qa/x_%d.png" "3,20,40,60"`

Stack (all local, zero cost, deterministic): Edge-TTS narration → faster-whisper
word alignment (mapped back onto the script text, so proper nouns never corrupt
captions) → Playwright/Edge canvas renderer at 1080×1920 @30 fps → ffmpeg H.264
+ procedural ambience (rumble/sonar or space drone), mixed to −14 LUFS.

### spec.json fields

| Field | Meaning |
|---|---|
| `script` | narration; drives duration, captions, stat anchors |
| `voice` / `voice_rate` | any edge-tts voice; `en-US-AndrewNeural` @ `-6%` ≈ 150 wpm deep male |
| `meter.eyebrow/unit/table` | top counter; `table` = `[fraction_of_speech, value]` piecewise-linear |
| `scenes` | `t0f/t1f` fractions of speech; painters: `water`, `walls`, `abyss`, `space`, `blackhole`, `warp`, `pulse` |
| `stats` | `at_word` anchors a headline to the spoken word; `eyebrow` + `lines` (auto-uppercased) |
| `ambience` | `deep` (rumble+sonar), `space` (drone+shimmer), `wind` |
| `meta.brand` | top-left logo block (change `AXIOM` to your channel name) |

### Scene painter params (cheatsheet)

- `water`: `top/bottom` hex, `rays` 0–1, `rayFade`, `snow` 0–1, `darken`, `glowBottom`
- `walls`: `speed` px/s, `rock`, `rock2`, `snow`, `glow`
- `abyss`: `flicker` n, `flickerColor`, `snow`, `life:true` (deep-fish silhouette), `glow`
- `space`: `nebulas[{x,y,r,color,a}]`, `stars`, `drift`
- `blackhole`: `r0/r1` horizon radius, `spin`, `diskColor`, `cy`, `stars`
- `warp`: `stars`, `glowColor` — star-streak tunnel
- `pulse`: `glowColor`, `ring`, `ringColor` — breathing ending card

## 4. Topic selection (maximum-traction science facts)

Pick topics with: **(a)** a second-person body stake, **(b)** a natural meter,
**(c)** a counterintuitive twist, **(d)** one huge number, **(e)** loop-able ending.
Proven queue:

1. Mariana Trench descent (built) — meter: DEPTH 0→10,935 M
2. Falling into a black hole (built) — meter: DISTANCE TO HORIZON 42,000,000→0 KM
3. Core of the Earth journey — DEPTH, "it's a solid ball of iron the size of the Moon"
4. Speed of light road trip — SPEED ↑, "you'd age 4 seconds, Earth ages 4 years"
5. Inside a volcano when it erupts — TEMPERATURE ↑
6. One day on each planet — TIME, "on Venus a day lasts longer than a year"
7. What if the Ocean disappeared — DEPTH of what's under
8. Absolute zero — TEMPERATURE ↓, "atoms stop… but not really"
9. 1 second inside a neutron star — DENSITY
10. Aging 1 billion years in 1 minute — TIME ↑ (heat death of the universe)

## 5. Posting strategy

- **Platforms**: YouTube Shorts + TikTok + Instagram Reels (English audience);
  Douyin/WeChat Channels need a re-cut with Chinese captions (engine supports any text).
- **Upload spec**: 1080×1920 H.264 (as rendered), loudness −14 LUFS (as mixed).
  Keep captions above y≈1600 — platform UI covers the bottom ~300 px.
- **Title formulas**: "What happens to your body at the bottom of the ocean",
  "This is what dying in a black hole feels like", "The deepest place on Earth".
- **Cadence**: 3–5/week; series consistency (same brand + meter device) trains recognition.
- **First comment**: pin the twist fact as a question to farm comments.
- **Retention levers built in**: 0.6 s narration start (no intro), meter open-loop,
  twist at ~45%, loop ending. Judge every video on 3 s retention + average % watched.

## 6. Fact-check ledger (both videos)

- Challenger Deep depth ≈ 10,935 m (2021 survey) ✓
- Sunlight (euphotic) zone ends ~200 m ✓; midnight (bathypelagic) zone 1,000–4,000 m ✓
- Pressure at bottom ≈ 1,086 bar ≈ 8 tons per square inch ✓
- Human body ≈ 60% water; water is nearly incompressible → no explosion ✓
- Hadal zone 6,000 m+, named after Hades ✓
- Deepest fish ever filmed: snailfish, 8,336 m, Izu-Ogasawara Trench, 2023 ✓
- Sgr A*: ~4 million solar masses ✓
- Time dilation/freeze at horizon, spaghettification for stellar-mass holes,
  painless crossing for supermassive, singularity as future spacetime event ✓
