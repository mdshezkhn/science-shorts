"""Procedural ambience beds + narration/ambience mix (numpy, no assets)."""
import subprocess, sys
import numpy as np

SR = 48000
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

def _write_wav(path, mono):
    from wave import open as wave_open
    pcm = (np.clip(mono, -1, 1) * 32767).astype("<i2")
    with wave_open(str(path), "w") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(pcm.tobytes())

def _noise(kind, n, seed=7):
    rng = np.random.default_rng(seed)
    if kind == "brown":
        out = np.cumsum(rng.standard_normal(n))
        out -= np.linspace(out[0], out[-1], n)  # detrend
        out /= (np.abs(out).max() + 1e-9)
        return out
    return rng.standard_normal(n)

def _lowpass(x, alpha):
    y = np.empty_like(x); acc = 0.0
    for i, v in enumerate(x):
        acc += alpha * (v - acc); y[i] = acc
    return y / (np.abs(y).max() + 1e-9)

def _lowpass_fft(x, cutoff_hz):
    X = np.fft.rfft(x)
    freqs = np.fft.rfftfreq(len(x), 1 / SR)
    X *= 1 / (1 + (freqs / cutoff_hz) ** 4)
    y = np.fft.irfft(X, len(x))
    return y / (np.abs(y).max() + 1e-9)

def _ping(freq, dur, decay=4.0):
    t = np.arange(int(SR * dur)) / SR
    return np.sin(2 * np.pi * freq * t) * np.exp(-decay * t)

def ambience(kind: str, dur: float, out_wav: str):
    n = int(SR * dur)
    t = np.arange(n) / SR
    out = np.zeros(n)
    if kind == "deep":  # abyssal rumble + sonar
        rumble = _lowpass_fft(_noise("brown", n, 3), 130) * 0.55
        swell = 0.6 + 0.4 * np.sin(2 * np.pi * t / 23.0)
        sub = np.sin(2 * np.pi * 38 * t) * 0.12 * (0.7 + 0.3 * np.sin(2 * np.pi * t / 31.0))
        out = rumble * swell + sub
        ping = _ping(620, 2.2, 3.2) * 0.10
        for start in np.arange(6, dur - 4, 9.5):
            i0 = int(start * SR); i1 = min(n, i0 + len(ping))
            out[i0:i1] += ping[: i1 - i0]
    elif kind == "space":  # detuned drone + shimmer
        out = (np.sin(2 * np.pi * 48 * t) + np.sin(2 * np.pi * 48.7 * t)) * 0.16
        out += np.sin(2 * np.pi * 96.5 * t) * 0.05 * (0.6 + 0.4 * np.sin(2 * np.pi * t / 17.0))
        shimmer = _noise("white", n, 11) * 0.5
        X = np.fft.rfft(shimmer)
        freqs = np.fft.rfftfreq(n, 1 / SR)
        band = ((freqs > 1800) & (freqs < 6500)).astype(float)
        X *= band
        shimmer = np.fft.irfft(X, n)
        shimmer /= (np.abs(shimmer).max() + 1e-9)
        out += shimmer * 0.028 * (0.6 + 0.4 * np.sin(2 * np.pi * t / 13.0))
    elif kind == "warm":  # nurture pad + crib-bell pings
        chords = [(110.0, 0.30), (164.81, 0.22), (220.0, 0.16), (277.18, 0.10)]
        pad = sum(np.sin(2 * np.pi * f * t + i) * a for i, (f, a) in enumerate(chords))
        out = pad * (0.75 + 0.25 * np.sin(2 * np.pi * t / 19.0))
        shimmer = _noise("white", n, 21)
        X = np.fft.rfft(shimmer)
        freqs = np.fft.rfftfreq(n, 1 / SR)
        X *= ((freqs > 2200) & (freqs < 7000)).astype(float)
        shimmer = np.fft.irfft(X, n)
        shimmer /= (np.abs(shimmer).max() + 1e-9)
        out += shimmer * 0.02 * (0.6 + 0.4 * np.sin(2 * np.pi * t / 15.0))
        for k, start in enumerate(np.arange(5, max(dur - 3, 6), 6.8)):
            f = 1318.5 if k % 2 == 0 else 1568.0
            ping = _ping(f, 2.6, 2.4) * 0.05
            i0 = int(start * SR); i1 = min(n, i0 + len(ping))
            out[i0:i1] += ping[: i1 - i0]
    elif kind == "wind":
        gust = 0.5 + 0.5 * np.sin(2 * np.pi * t / 11.0 + 1.2)
        out = _lowpass_fft(_noise("white", n, 5), 500) * (0.25 + 0.3 * gust)
    _write_wav(out_wav, out * 0.9)
    return out_wav

def mix(narr_wav, amb_wav, out_wav, narr_gain=1.0, amb_gain=0.32, narr_delay=0.7, total=None):
    def rd(p):
        raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(p), "-f", "f32le",
                              "-ac", "1", "-ar", str(SR), "-"], capture_output=True).stdout
        return np.frombuffer(raw, dtype=np.float32).copy()
    narr, amb = rd(narr_wav), rd(amb_wav)
    dur = total if total else (len(narr) / SR + narr_delay + 1.0)
    n = int(SR * dur)
    out = np.zeros(n)
    i0 = int(narr_delay * SR)
    i1 = min(n, i0 + len(narr))
    out[i0:i1] += narr[: i1 - i0] * narr_gain
    out[: min(n, len(amb))] += amb[: min(n, len(amb))] * amb_gain
    # gentle bed fade-out over last 2.5 s
    f = int(2.5 * SR)
    out[-f:] *= np.linspace(1, 0, f)
    peak = np.abs(out).max()
    if peak > 0.89:
        out *= 0.89 / peak
    _write_wav(out_wav, out)
    return out_wav
