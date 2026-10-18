#!/usr/bin/env python3
"""Detecta texto que queda fuera de todo panel (solo dentro del lienzo)."""
import html as htmllib
import json
import pathlib
import re
import subprocess
import tempfile

IMG = pathlib.Path(__file__).resolve().parent.parent / "img"

JS = r"""
const out = [];
for (const svg of document.querySelectorAll('svg')) {
  const vb = svg.viewBox.baseVal;
  const canvasArea = vb.width * vb.height;
  const rects = [...svg.querySelectorAll('rect')]
    .map(r => { const b = r.getBBox(); return {b, area: b.width * b.height}; })
    .filter(o => o.b.width > 1 && o.b.height > 1);

  for (const t of svg.querySelectorAll('text')) {
    const b = t.getBBox();
    const startX = b.x, startY = b.y + b.height / 2;
    let best = null;
    for (const o of rects) {
      const r = o.b;
      if (startX >= r.x - 0.5 && startX <= r.x + r.width + 0.5 &&
          startY >= r.y - 0.5 && startY <= r.y + r.height + 0.5) {
        if (!best || o.area < best.area) best = o;
      }
    }
    if (!best) continue;
    // el rect contenedor es el lienzo completo => el texto flota fuera de todo panel
    if (best.area > canvasArea * 0.85) {
      out.push({
        svg: svg.id,
        texto: (t.textContent || '').trim().slice(0, 64),
        pos: [b.x.toFixed(0), b.y.toFixed(0)].join(',')
      });
    }
  }
}
const pre = document.createElement('pre');
pre.id = 'RESULT';
pre.textContent = JSON.stringify(out);
document.body.appendChild(pre);
"""

malos = 0
for svg in sorted(IMG.glob("*.svg")):
    content = svg.read_text(encoding="utf-8").replace("<svg ", f'<svg id="{svg.stem}" ', 1)
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"></head><body>{content}
<script>{JS}</script></body></html>"""
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, dir=IMG) as f:
        f.write(html)
        tmp = f.name
    res = subprocess.run(
        ["chromium", "--headless", "--disable-gpu", "--no-sandbox",
         "--virtual-time-budget=4000", "--dump-dom", f"file://{tmp}"],
        capture_output=True, text=True)
    pathlib.Path(tmp).unlink(missing_ok=True)
    m = re.search(r'<pre id="RESULT">(.*?)</pre>', res.stdout, re.S)
    if not m:
        continue
    data = json.loads(htmllib.unescape(m.group(1)))
    if data:
        print(f"\n=== {svg.name} ===")
        for d in data:
            malos += 1
            print(f"  FUERA DE PANEL  pos[{d['pos']}]  \"{d['texto']}\"")
    else:
        print(f"{svg.name}: todo el texto dentro de un panel")

print(f"\nTextos flotando fuera de panel: {malos}")
