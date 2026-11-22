"""Synthesize the 32s make.fun bounty clip entirely from generated frames.

Only the Python standard library, Pillow and imageio_ffmpeg's bundled ffmpeg
binary are used. Frames are piped to ffmpeg as raw rgb24; no intermediate
video rendering library is required.

Scenes:
  0.0 - 3.0   hook ("I gave an AI one sentence. It built a game.")
  3.0 - 7.0   the one-sentence prompt, typed verbatim
  7.0 - 18.0  the agent "working": real game/main.js lines appear
 18.0 - 27.0  the finished game running in a browser
 27.0 - 29.5  CTA: "Come build on make.fun"
 29.5 - 32.0  official card16.webm with our referral code typed in
"""

from __future__ import annotations

import math
import random
import re
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont
import imageio_ffmpeg

ROOT = Path(__file__).resolve().parent
CARD = ROOT / "assets" / "card16.webm"
SOURCE = ROOT / "game" / "main.js"
OUT = ROOT / "build" / "postx_agent_builds_a_game.mp4"
OVERLAY_ARTIFACT = ROOT / "assets" / "referral_overlay.png"

W, H, FPS, DURATION = 1280, 720, 30, 32.0
TOTAL = int(FPS * DURATION)

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()

PINK = (196, 27, 130)
CYAN = (55, 224, 216)
WHITE = (255, 255, 255)
MUTED = (154, 144, 166)
INK = (12, 11, 20)
CODE = "jhbwqchj"

FONT_FILES = {
    "sans": ["C:/Windows/Fonts/arial.ttf", "arial.ttf"],
    "bold": ["C:/Windows/Fonts/arialbd.ttf", "arialbd.ttf"],
    "mono": ["C:/Windows/Fonts/consola.ttf", "consola.ttf"],
    "monobold": ["C:/Windows/Fonts/consolab.ttf", "consolab.ttf"],
}


def font(kind: str, size: int) -> ImageFont.FreeTypeFont:
    for candidate in FONT_FILES[kind]:
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            continue
    return ImageFont.load_default(size)


def mix(a, b, p):
    p = max(0.0, min(1.0, p))
    return tuple(int(round(x + (y - x) * p)) for x, y in zip(a, b))


def vertical_gradient(top, bottom):
    img = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(img)
    for y in range(H):
        d.line([(0, y), (W, y)], fill=mix(top, bottom, y / (H - 1)))
    return img


def glow(base, center, radius, color, strength=0.32):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(layer).ellipse(
        [center[0] - radius, center[1] - radius,
         center[0] + radius, center[1] + radius],
        fill=(*color, int(255 * strength)),
    )
    layer = layer.filter(ImageFilter.GaussianBlur(radius // 2))
    return Image.alpha_composite(base.convert("RGBA"), layer).convert("RGB")


# --------------------------------------------------------------------------
# Static backgrounds (built once, copied per frame)
# --------------------------------------------------------------------------
BG_HOOK = glow(vertical_gradient((10, 8, 18), (34, 10, 36)),
               (640, 360), 360, PINK, 0.22)
BG_PROMPT = vertical_gradient((9, 10, 18), (18, 14, 28))
BG_CODE = vertical_gradient((9, 9, 16), (17, 12, 24))
BG_GAME = vertical_gradient((9, 10, 17), (25, 13, 31))
BG_CTA = glow(vertical_gradient((154, 16, 102), (196, 27, 130)),
              (640, 300), 420, (255, 120, 200), 0.18)

# Faint grid on the prompt/code/game backgrounds.
for _bg in (BG_PROMPT, BG_CODE, BG_GAME):
    _d = ImageDraw.Draw(_bg, "RGBA")
    for _x in range(0, W, 40):
        _d.line([(_x, 0), (_x, H)], fill=(255, 255, 255, 6))
    for _y in range(0, H, 40):
        _d.line([(0, _y), (W, _y)], fill=(255, 255, 255, 6))

# --------------------------------------------------------------------------
# Scene 1: hook
# --------------------------------------------------------------------------
HOOK_LINE = "I gave an AI one sentence."
PAYOFF = "It built a game."


def scene_hook(img, t):
    d = ImageDraw.Draw(img)
    d.text((640, 105), "ONE SENTENCE  →  ONE GAME",
           font=font("bold", 20), fill=MUTED, anchor="mm")

    shown = int(max(0, min(len(HOOK_LINE), (t - 0.20) / 0.052)))
    f = font("bold", 56)
    d.text((640, 268), HOOK_LINE[:shown], font=f, fill=WHITE, anchor="mm")
    if shown < len(HOOK_LINE) and int(t * 9) % 2 == 0:
        tw = f.getlength(HOOK_LINE[:shown])
        d.rectangle([640 - tw / 2 + 3, 241, 640 - tw / 2 + 6, 295], fill=PINK)

    if t >= 1.50:
        p = min(1.0, (t - 1.50) / 0.30)
        size = int(66 + 12 * p)
        d.text((640, 388), PAYOFF, font=font("bold", size),
               fill=mix(WHITE, PINK, 0.35 + 0.65 * p), anchor="mm")

    if t >= 2.05:
        width = int(min(430, (t - 2.05) * 2400))
        d.rounded_rectangle([640 - width / 2, 455, 640 + width / 2, 461],
                            radius=3, fill=PINK)

    d.text((640, 660), "make.fun", font=font("bold", 22),
           fill=mix(MUTED, PINK, 0.5), anchor="mm")


# --------------------------------------------------------------------------
# Scene 2: the prompt
# --------------------------------------------------------------------------
PROMPT_LINES = [
    "Build a game where I dodge falling blocks",
    "with the arrow keys. My score goes up",
    "the longer I survive.",
]
PROMPT_FULL = " ".join(PROMPT_LINES)


def scene_prompt(img, t):
    d = ImageDraw.Draw(img)
    d.text((150, 82), "THE PROMPT", font=font("bold", 26),
           fill=PINK, anchor="lm")
    d.text((150, 116), "one sentence, verbatim", font=font("sans", 17),
           fill=MUTED, anchor="lm")

    box = (150, 165, 1130, 535)
    d.rounded_rectangle(box, radius=16, fill=(20, 19, 30),
                        outline=(74, 55, 88), width=2)
    d.rounded_rectangle((150, 165, 1130, 218), radius=16, fill=(40, 30, 50))
    d.rectangle((150, 200, 1130, 218), fill=(40, 30, 50))
    for i, col in enumerate(((232, 96, 124), (232, 176, 84), (86, 200, 150))):
        d.ellipse([178 + i * 26, 184, 190 + i * 26, 196], fill=col)
    d.text((280, 191), "prompt.txt", font=font("mono", 15),
           fill=MUTED, anchor="lm")

    shown = int(max(0, min(len(PROMPT_FULL), (t - 3.40) / 0.028)))
    remaining = shown
    for i, line in enumerate(PROMPT_LINES):
        take = max(0, min(len(line), remaining))
        d.text((200, 268 + i * 58), line[:take],
               font=font("mono", 27), fill=WHITE)
        remaining -= len(line) + (1 if i < len(PROMPT_LINES) - 1 else 0)
        if take == len(line) and remaining <= 0 and int(t * 8) % 2 == 0:
            x = 200 + font("mono", 27).getlength(line)
            d.rectangle([x + 3, 268 + i * 58, x + 8, 268 + i * 58 + 32],
                        fill=PINK)

    if t >= 6.45:
        p = min(1.0, (t - 6.45) / 0.25)
        d.text((640, 598), "That's the entire brief.",
               font=font("sans", 26), fill=mix(MUTED, WHITE, p), anchor="mm")


# --------------------------------------------------------------------------
# Scene 3: agent working (real source lines stream in)
# --------------------------------------------------------------------------
KEYWORDS = re.compile(
    r"(\"[^\"]*\"|'[^']*'|\b(?:const|let|var|function|if|else|for|return|"
    r"new|true|false|null)\b)"
)

_src_lines = SOURCE.read_text(encoding="utf-8").splitlines()
CODE_LINES = [(i + 1, line) for i, line in enumerate(_src_lines) if line.strip()]
VISIBLE_LINES = 25


def draw_colored_code(d, xy, text, f):
    if text.lstrip().startswith(("//", "/*", "*")):
        d.text(xy, text, font=f, fill=(112, 103, 128))
        return
    x, y = xy
    pos = 0
    for m in KEYWORDS.finditer(text):
        if m.start() > pos:
            seg = text[pos:m.start()]
            d.text((x, y), seg, font=f, fill=(214, 212, 226))
            x += f.getlength(seg)
        tok = m.group()
        color = (236, 104, 180) if tok[0] in "\"'" else CYAN
        d.text((x, y), tok, font=f, fill=color)
        x += f.getlength(tok)
        pos = m.end()
    if pos < len(text):
        d.text((x, y), text[pos:], font=f, fill=(214, 212, 226))


def scene_code(img, t):
    d = ImageDraw.Draw(img)
    box = (70, 96, 1210, 692)
    d.rounded_rectangle(box, radius=14, fill=(16, 15, 25),
                        outline=(74, 55, 88), width=2)
    d.rounded_rectangle((70, 96, 1210, 152), radius=14, fill=(38, 29, 48))
    d.rectangle((70, 138, 1210, 152), fill=(38, 29, 48))
    for i, col in enumerate(((232, 96, 124), (232, 176, 84), (86, 200, 150))):
        d.ellipse([96 + i * 24, 116, 108 + i * 24, 128], fill=col)
    d.text((200, 124), "agent@make.fun  —  writing game/main.js",
           font=font("mono", 16), fill=WHITE, anchor="lm")
    pulse = 0.45 + 0.55 * abs(math.sin(t * 4))
    d.text((1180, 124), "● BUILDING", font=font("monobold", 15),
           fill=mix(MUTED, PINK, pulse), anchor="rm")

    count = int(max(0, min(len(CODE_LINES), (t - 7.15) / 0.070)))
    start = max(0, count - VISIBLE_LINES)
    mono = font("mono", 16)
    for j, (lineno, text) in enumerate(CODE_LINES[start:count]):
        y = 166 + j * 20
        d.text((108, y), str(lineno).rjust(3), font=font("mono", 13),
               fill=(96, 88, 112), anchor="la")
        draw_colored_code(d, (152, y), text, mono)

    if count > 0 and count < len(CODE_LINES) and int(t * 6) % 2 == 0:
        y = 166 + (count - start) * 20
        d.rectangle([152, y, 160, y + 18], fill=PINK)

    pct = count / len(CODE_LINES)
    d.rounded_rectangle([108, 668, 1172, 680], radius=6, fill=(44, 36, 56))
    if pct > 0:
        d.rounded_rectangle([108, 668, 108 + int(1064 * pct), 680],
                            radius=6, fill=PINK)
    d.text((108, 648), "generating game/main.js  ·  %d%%" % int(pct * 100),
           font=font("mono", 14), fill=MUTED, anchor="la")


# --------------------------------------------------------------------------
# Scene 4: the finished game, running
# --------------------------------------------------------------------------
_rng = random.Random(1709)
FALLING = []
for _i in range(46):
    FALLING.append({
        "spawn": 18.0 + _i * 0.195,
        "x": _rng.randrange(0, 920),
        "w": _rng.randrange(28, 56),
        "vy": _rng.randrange(165, 285),
        "color": PINK if _i % 3 else CYAN,
        "angle": _rng.uniform(-0.4, 0.4),
    })

CANVAS = (187, 176, 906, 510)  # x, y, w, h (16:9)


def game_frame(t):
    """Render a 960x540 frame that mirrors game/main.js."""
    im = Image.new("RGB", (960, 540), (11, 11, 19))
    d = ImageDraw.Draw(im)
    for x in range(0, 960, 40):
        d.line([(x, 0), (x, 540)], fill=(22, 21, 33))
    for y in range(0, 540, 40):
        d.line([(0, y), (960, y)], fill=(22, 21, 33))

    elapsed = t - 18.0
    for b in FALLING:
        age = elapsed - (b["spawn"] - 18.0)
        if age < 0:
            continue
        y = -b["w"] + age * b["vy"]
        if y > 539:
            continue
        d.rectangle([b["x"], y, b["x"] + b["w"], y + b["w"]],
                    fill=b["color"])
        d.rectangle([b["x"], y, b["x"] + b["w"], min(539, y + 5)],
                    fill=mix(b["color"], WHITE, 0.55))

    px = 480 + math.sin(elapsed * 1.7) * 300 + math.sin(elapsed * 0.63) * 60
    px = max(0, min(914, px))
    d.rectangle([px, 468, px + 46, 514], fill=WHITE, outline=PINK, width=3)
    d.rectangle([px - 8, 516, px + 54, 519], fill=mix(PINK, (60, 20, 50), 0.4))

    score = max(0, int(elapsed * 10))
    d.text((20, 18), "SCORE " + str(score).zfill(3),
           font=font("monobold", 24), fill=PINK, anchor="la")
    d.text((940, 20), "← → / A D", font=font("mono", 17),
           fill=MUTED, anchor="ra")
    return im


def scene_game(img, t):
    d = ImageDraw.Draw(img)
    d.text((640, 52), "THE FINISHED GAME — RUNNING IN A BROWSER",
           font=font("bold", 25), fill=WHITE, anchor="mm")
    d.text((640, 84), "Open index.html. Press space. Dodge. Survive.",
           font=font("sans", 17), fill=MUTED, anchor="mm")

    d.rounded_rectangle((120, 112, 1160, 692), radius=14,
                        fill=(26, 24, 38), outline=(74, 55, 88), width=2)
    d.rounded_rectangle((120, 112, 1160, 166), radius=14, fill=(44, 34, 54))
    d.rectangle((120, 152, 1160, 166), fill=(44, 34, 54))
    for i, col in enumerate(((232, 96, 124), (232, 176, 84), (86, 200, 150))):
        d.ellipse([146 + i * 24, 130, 158 + i * 24, 142], fill=col)
    d.text((250, 139), "file:///.../game/index.html  —  DODGE",
           font=font("mono", 15), fill=MUTED, anchor="lm")
    if int(t * 2.5) % 2 == 0:
        d.text((1136, 139), "● LIVE", font=font("monobold", 14),
               fill=PINK, anchor="rm")

    x, y, w, h = CANVAS
    frame = game_frame(t).resize((w, h), Image.Resampling.BILINEAR)
    img.paste(frame, (x, y))
    d = ImageDraw.Draw(img)
    d.rectangle((x, y, x + w, y + h), outline=(74, 55, 88), width=2)


# --------------------------------------------------------------------------
# Scene 5: CTA
# --------------------------------------------------------------------------
def scene_cta(img, t):
    d = ImageDraw.Draw(img)
    d.text((640, 96), "YOUR TURN", font=font("bold", 22),
           fill=(255, 226, 242), anchor="mm")
    d.text((640, 268), "Come build", font=font("bold", 94),
           fill=WHITE, anchor="mm")
    d.text((640, 384), "on make.fun", font=font("bold", 94),
           fill=WHITE, anchor="mm")

    width = int(min(560, max(0, (t - 27.4) * 1700)))
    d.rounded_rectangle([640 - width / 2, 466, 640 + width / 2, 473],
                        radius=3, fill=(255, 255, 255))

    p = min(1.0, max(0.0, (t - 27.65) / 0.4))
    d.text((640, 540), "Your agent can ship one too.",
           font=font("sans", 28), fill=mix((255, 205, 230), WHITE, p),
           anchor="mm")
    d.text((640, 660), "make.fun", font=font("bold", 22),
           fill=(255, 225, 242), anchor="mm")


# --------------------------------------------------------------------------
# Card overlays: transparent PNGs with the referral code typed at the field
# --------------------------------------------------------------------------
def build_overlays(tmp):
    out = {}
    ov_dir = tmp / "overlays"
    ov_dir.mkdir(parents=True, exist_ok=True)
    f = font("sans", 41)  # 41px, colour #191419, coords in 1280x720 space
    for k in range(len(CODE) + 1):
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(layer).text((288, 463), CODE[:k], font=f,
                                   fill=(25, 20, 25, 255))
        path = ov_dir / ("overlay_%02d.png" % k)
        layer.save(path)
        out[k] = layer
    # Keep the finished, paste-ready overlay as a visible artifact too.
    out[len(CODE)].save(OVERLAY_ARTIFACT)
    return out


def decode_card_frames(tmp):
    card_dir = tmp / "card"
    card_dir.mkdir(parents=True, exist_ok=True)
    cmd = [
        FFMPEG, "-y", "-loglevel", "error", "-i", str(CARD),
        "-vf", "scale=1280:720,fps=30", "-frames:v", "75",
        "-pix_fmt", "rgb24", str(card_dir / "card_%03d.png"),
    ]
    subprocess.run(cmd, check=True)
    frames = sorted(card_dir.glob("card_*.png"))
    if len(frames) < 75:
        raise RuntimeError("expected 75 card frames, got %d" % len(frames))
    return frames


# --------------------------------------------------------------------------
# Encode
# --------------------------------------------------------------------------
def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    print("ffmpeg:", FFMPEG)
    print("source lines available for reveal:", len(CODE_LINES))
    print("rendering", TOTAL, "frames ->", OUT)

    with tempfile.TemporaryDirectory(prefix="postx_frames_") as td:
        tmp = Path(td)
        overlays = build_overlays(tmp)
        card_frames = decode_card_frames(tmp)

        cmd = [
            FFMPEG, "-y", "-loglevel", "error",
            "-f", "rawvideo", "-pix_fmt", "rgb24",
            "-s", "%dx%d" % (W, H), "-r", str(FPS),
            "-i", "pipe:0", "-an",
            "-c:v", "libx264", "-preset", "fast", "-crf", "20",
            "-pix_fmt", "yuv420p", "-movflags", "+faststart",
            str(OUT),
        ]
        log_path = ROOT / "build" / "ffmpeg.log"
        with log_path.open("w", encoding="utf-8") as log:
            proc = subprocess.Popen(cmd, stdin=subprocess.PIPE,
                                    stdout=subprocess.DEVNULL, stderr=log)
            try:
                for i in range(TOTAL):
                    t = i / FPS
                    if t < 3.0:
                        img = BG_HOOK.copy()
                        scene_hook(img, t)
                    elif t < 7.0:
                        img = BG_PROMPT.copy()
                        scene_prompt(img, t)
                    elif t < 18.0:
                        img = BG_CODE.copy()
                        scene_code(img, t)
                    elif t < 27.0:
                        img = BG_GAME.copy()
                        scene_game(img, t)
                    elif t < 29.5:
                        img = BG_CTA.copy()
                        scene_cta(img, t)
                    else:
                        idx = min(74, int((t - 29.5) * FPS))
                        with Image.open(card_frames[idx]) as cf:
                            rgba = cf.convert("RGBA")
                        typed = min(len(CODE), int((t - 29.5) / 0.105))
                        img = Image.alpha_composite(
                            rgba, overlays[typed]).convert("RGB")

                    proc.stdin.write(img.tobytes())
                    if (i + 1) % 240 == 0:
                        print("  %4d/%d frames (%.1fs)" % (i + 1, TOTAL, t))
            finally:
                proc.stdin.close()
            rc = proc.wait()
    if rc != 0:
        raise RuntimeError("ffmpeg failed (%d); see %s" % (rc, log_path))
    print("done:", OUT, "bytes:", OUT.stat().st_size)


if __name__ == "__main__":
    main()
