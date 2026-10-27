"""Frame-stepped renderer: Playwright (msedge) screenshots -> ffmpeg pipe -> MP4."""
import json, subprocess, sys, os
from pathlib import Path

ENGINE = Path(__file__).parent
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

def render(spec: dict, out_mp4: str, audio_wav: str | None = None, fps: int = 30, jpeg_q: int = 92):
    from playwright.sync_api import sync_playwright
    duration = spec["duration"]
    n_frames = int(round(duration * fps)) + 1
    html = (ENGINE / "render.html").resolve().as_uri()

    vf = ["-c:v", "libx264", "-preset", "medium", "-crf", "19",
          "-pix_fmt", "yuv420p", "-r", str(fps), "-movflags", "+faststart"]
    cmd = ["ffmpeg", "-y", "-v", "error",
           "-f", "image2pipe", "-framerate", str(fps), "-i", "-"]
    if audio_wav:
        cmd += ["-i", audio_wav, "-map", "0:v", "-map", "1:a",
                "-c:a", "aac", "-b:a", "160k",
                "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-shortest"]
    cmd += vf + [out_mp4]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)

    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel="msedge", headless=True,
                                     args=["--force-device-scale-factor=1", "--hide-scrollbars"])
        page = browser.new_page(viewport={"width": 1080, "height": 1920}, device_scale_factor=1)
        page.goto(html)
        page.evaluate("s => window.setSpec(s)", spec)
        page.wait_for_function("window.READY===true", timeout=10000)
        # force-load web fonts before first screenshot
        page.evaluate("async () => { await Promise.all([document.fonts.load('700 104px Oswald'), document.fonts.load('500 34px Oswald'), document.fonts.load('400 42px Oswald'), document.fonts.load('46px Georgia')]); }")
        page.evaluate("() => window.renderFrame(0)")  # warm-up (font layout caches)
        for i in range(n_frames):
            page.evaluate("t => window.renderFrame(t)", i / fps)
            png = page.screenshot(type="jpeg", quality=jpeg_q)
            proc.stdin.write(png)
            if i % 300 == 0:
                print(f"  frame {i}/{n_frames}", flush=True)
        browser.close()
    proc.stdin.close()
    proc.wait()
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg failed rc={proc.returncode}")
    print(f"RENDERED {out_mp4} ({n_frames} frames, {duration:.1f}s)")

if __name__ == "__main__":
    spec = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    out = sys.argv[2]
    audio = sys.argv[3] if len(sys.argv) > 3 else None
    if out.endswith(".png"):
        # stills mode: render.py spec.json "out_%d.png" "0,5,12,30"
        from playwright.sync_api import sync_playwright
        times = [float(x) for x in (sys.argv[3] if len(sys.argv) > 3 else "0,10,30").split(",")]
        html = (ENGINE / "render.html").resolve().as_uri()
        with sync_playwright() as pw:
            browser = pw.chromium.launch(channel="msedge", headless=True)
            page = browser.new_page(viewport={"width": 1080, "height": 1920}, device_scale_factor=1)
            page.goto(html)
            page.evaluate("s => window.setSpec(s)", spec)
            page.wait_for_function("window.READY===true", timeout=10000)
            page.evaluate("async () => { await Promise.all([document.fonts.load('700 104px Oswald'), document.fonts.load('500 34px Oswald'), document.fonts.load('400 42px Oswald'), document.fonts.load('46px Georgia')]); }")
            for k, t in enumerate(times):
                page.evaluate("t => window.renderFrame(t)", t)
                page.screenshot(path=out % (k + 1), type="png")
                print(f"still t={t}s -> {out % (k + 1)}")
            browser.close()
    else:
        render(spec, out, audio)
