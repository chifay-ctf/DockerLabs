#!/usr/bin/env python3
"""Convierte los SVG de img/ a PNG con Chromium headless.

Chromium respeta el CSS embebido y el escalado por device-pixel-ratio, que es
justo lo que necesitan estos diagramas. La versión anterior dependía de
librsvg (namespace Rsvg), que no está instalado en este equipo.
"""
import pathlib
import re
import subprocess

ROOT = pathlib.Path(__file__).resolve().parent.parent
IMG = ROOT / "img"
SCALE = 2

for svg in sorted(IMG.glob("*.svg")):
    text = svg.read_text(encoding="utf-8")
    m = re.search(r'viewBox="0 0 (\d+) (\d+)"', text)
    if not m:
        m = re.search(r'width="(\d+)" height="(\d+)"', text)
    w, h = int(m.group(1)), int(m.group(2))
    out = svg.with_suffix(".png")
    cmd = [
        "chromium", "--headless", "--no-sandbox", "--disable-gpu",
        "--hide-scrollbars", f"--force-device-scale-factor={SCALE}",
        f"--window-size={w},{h}", f"--screenshot={out}", svg.as_uri(),
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    print(f"{svg.name} -> {out.name} ({w * SCALE}x{h * SCALE})")
