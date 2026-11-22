"""Verify the encoded video and pull a contact sheet of representative frames."""
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg

ROOT = Path(__file__).resolve().parent
VIDEO = ROOT / "build" / "postx_agent_builds_a_game.mp4"
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()

probe = subprocess.run([FFMPEG, "-hide_banner", "-i", str(VIDEO)],
                       capture_output=True, text=True)
print(probe.stderr)

times = [1.5, 5.2, 12.0, 23.0, 28.6, 31.2]
sheet_dir = ROOT / "build" / "checks"
sheet_dir.mkdir(parents=True, exist_ok=True)
shots = []
for t in times:
    path = sheet_dir / ("t%05.1f.png" % t)
    subprocess.run([
        FFMPEG, "-y", "-loglevel", "error", "-ss", str(t),
        "-i", str(VIDEO), "-frames:v", "1", str(path),
    ], check=True)
    shots.append((t, path))

thumb_w, thumb_h = 640, 360
sheet = Image.new("RGB", (thumb_w * 2, (thumb_h + 30) * 3), (16, 14, 22))
d = ImageDraw.Draw(sheet)
try:
    f = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 18)
except OSError:
    f = ImageFont.load_default()
for i, (t, path) in enumerate(shots):
    x, y = (i % 2) * thumb_w, (i // 2) * (thumb_h + 30)
    with Image.open(path) as im:
        sheet.paste(im.convert("RGB").resize((thumb_w, thumb_h)), (x, y))
    d.text((x + 8, y + thumb_h + 5), "t=%.1fs" % t, font=f, fill=(255, 255, 255))
sheet_path = sheet_dir / "contact_sheet.png"
sheet.save(sheet_path)
print("contact sheet:", sheet_path, sheet_path.stat().st_size)
print("video bytes:", VIDEO.stat().st_size)
