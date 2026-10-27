"""Build orchestrator: script -> TTS -> align -> spec assembly -> render -> mix."""
import json, sys, subprocess
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(Path(__file__).parent))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import tts as T
import audio as A
import render as R

BREAK = set(".!?—:")

def _norm(w):
    import re
    return re.sub(r"[^\w\-]", "", w.lower())

def script_timed_words(script, whisper_words):
    """Assign whisper timings to the SCRIPT's own words (fixes ASR text errors).
    Uses difflib opcodes: equal -> reuse timing; replace/delete spans -> interpolate."""
    import difflib
    sw = script.split()
    sn = [_norm(x) for x in sw]
    wn = [_norm(w["text"]) for w in whisper_words]
    out = [None] * len(sw)
    sm = difflib.SequenceMatcher(None, sn, wn, autojunk=False)
    last_t = whisper_words[-1]["t1"] if whisper_words else 0.0
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            for k in range(i2 - i1):
                out[i1 + k] = {"t0": whisper_words[j1 + k]["t0"],
                               "t1": whisper_words[j1 + k]["t1"],
                               "text": sw[i1 + k]}
        else:
            n = i2 - i1
            if n == 0:
                continue
            t0 = whisper_words[j1]["t0"] if j2 > j1 else (whisper_words[j1 - 1]["t1"] if j1 > 0 else 0.0)
            t1 = whisper_words[j2 - 1]["t1"] if j2 > j1 else (whisper_words[j1]["t0"] if j1 < len(whisper_words) else last_t)
            if t1 <= t0:
                t1 = t0 + 0.08 * n
            for k in range(n):
                out[i1 + k] = {"t0": t0 + (t1 - t0) * k / n,
                               "t1": t0 + (t1 - t0) * (k + 1) / n,
                               "text": sw[i1 + k]}
    return [w for w in out if w]

def group_captions(words, max_words=6):
    """Group aligned words into caption phrases at punctuation / length limits."""
    caps, cur = [], []
    for w in words:
        cur.append(w)
        tail = w["text"]
        if (tail and tail[-1] in BREAK) or len(cur) >= max_words:
            caps.append(cur); cur = []
    if cur:
        if caps and len(cur) <= 2:
            caps[-1].extend(cur)
        else:
            caps.append(cur)
    out = []
    for grp in caps:
        out.append({"t0": grp[0]["t0"], "t1": grp[-1]["t1"] + 0.12, "words": grp})
    # merge micro-captions (<0.7s) into neighbours
    merged = []
    for c in out:
        if merged and (c["t1"] - c["t0"]) < 0.7:
            merged[-1]["words"].extend(c["words"])
            merged[-1]["t1"] = c["t1"]
        else:
            merged.append(c)
    return merged

def build(spec_path: str, skip_render=False):
    spec = json.loads(Path(spec_path).read_text(encoding="utf-8"))
    vid = spec["id"]
    work = ROOT / "work" / vid
    work.mkdir(parents=True, exist_ok=True)
    print(f"== BUILD {vid} ==")

    # typography: standalone em-dashes become commas (cleaner captions, same TTS pause)
    spec["script"] = spec["script"].replace(" — ", ", ").replace("—", " ")

    # 1) narration
    voice = spec.get("voice", "en-US-AndrewNeural")
    rate = spec.get("voice_rate", "-6%")
    mp3 = work / "narration.mp3"
    if not mp3.exists():
        T.synth(spec["script"], voice, str(mp3), rate)
        print("  TTS ok")
    wav = T.to_wav(mp3, work / "narration.wav")

    # 2) word alignment (whisper timings mapped onto script's own words)
    raw_words = T.align_words(wav)
    words = script_timed_words(spec["script"], raw_words)
    speech_dur = words[-1]["t1"]
    tail = spec.get("tail", 2.6)
    duration = speech_dur + tail
    print(f"  {len(words)} words, speech {speech_dur:.1f}s, video {duration:.1f}s")

    # 3) assemble render spec
    rspec = {
        "duration": round(duration, 2),
        "speechDur": round(speech_dur, 2),
        "meta": spec["meta"],
        "meter": spec["meter"],
        "captions": [
            {"t0": c["t0"], "t1": min(c["t1"], duration),
             "words": [{"t0": w["t0"], "text": w["text"]} for w in c["words"]]}
            for c in group_captions(words)
        ],
        "scenes": [],
        "stats": [],
    }
    for sc in spec["scenes"]:
        rspec["scenes"].append({"type": sc["type"], "t0f": sc["t0f"], "t1f": sc["t1f"],
                                "params": sc.get("params", {})})
    for st in spec["stats"]:
        t0 = st.get("atf", 0.5) * speech_dur
        if "at_word" in st:
            key = st["at_word"].lower()
            hit = next((w for w in words if key in w["text"].lower()), None)
            if hit:
                t0 = hit["t0"] + st.get("offset", -0.15)
        rspec["stats"].append({"t0": round(max(0, t0), 2), "dur": st.get("dur", 3.8),
                               "eyebrow": st["eyebrow"], "lines": st["lines"]})

    spec_file = work / "render_spec.json"
    spec_file.write_text(json.dumps(rspec), encoding="utf-8")

    if skip_render:
        print("  (spec written, render skipped)")
        return

    # 4) render video
    silent = work / "video.mp4"
    R.render(rspec, str(silent))

    # 5) audio bed + final mux
    amb = A.ambience(spec.get("ambience", "deep"), duration, str(work / "amb.wav"))
    mixw = A.mix(wav, amb, str(work / "final_audio.wav"),
                 amb_gain=spec.get("amb_gain", 0.32), total=duration)
    out = ROOT / "out" / f"{vid}.mp4"
    out.parent.mkdir(exist_ok=True)
    # re-mux rendered video with final mix (render() already muxed narration; replace audio)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(silent), "-i", mixw,
                    "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac",
                    "-b:a", "192k", "-movflags", "+faststart", str(out)], check=True)
    print(f"DONE -> {out}")

if __name__ == "__main__":
    build(sys.argv[1], skip_render="--spec-only" in sys.argv)
