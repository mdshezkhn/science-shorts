"""Narration synthesis (edge-tts) + word-level alignment (faster-whisper)."""
import asyncio, subprocess, sys, tempfile
from pathlib import Path
import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

def load_audio(path, sr=16000):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path),
                          "-f", "f32le", "-ac", "1", "-ar", str(sr), "-"],
                         capture_output=True).stdout
    return np.frombuffer(raw, dtype=np.float32).copy(), sr

def synth(text: str, voice: str, out_mp3: str, rate: str = "-6%"):
    import edge_tts
    async def run():
        c = edge_tts.Communicate(text, voice, rate=rate)
        await c.save(out_mp3)
    asyncio.run(run())
    return out_mp3

def to_wav(src, dst, sr=48000):
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(src),
                    "-ar", str(sr), "-ac", "2", str(dst)], check=True)
    return dst

def align_words(audio_path, model_size="base.en"):
    """-> list of {t0,t1,text} word timings."""
    from faster_whisper import WhisperModel
    m = WhisperModel(model_size, device="cpu", compute_type="int8")
    audio, _ = load_audio(audio_path)
    segs, _ = m.transcribe(audio, language="en", word_timestamps=True)
    words = []
    for s in segs:
        for w in (s.words or []):
            words.append({"t0": round(w.start, 3), "t1": round(w.end, 3), "text": w.word.strip()})
    return words
