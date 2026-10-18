#!/usr/bin/env python3
"""Verificador de desbordes de texto en los SVG (getBBox() real del motor)."""
import html as htmllib
import xml.dom.minidom
import json
import pathlib
import re
import subprocess
import sys
import tempfile

IMG = pathlib.Path(__file__).resolve().parent.parent / "img"
UMBRAL = 3.0

JS = r"""
const out = [];
for (const svg of document.querySelectorAll('svg')) {
  const name = svg.id;
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
    const issues = [];
    if (best) {
      const r = best.b;
      const dr = (b.x + b.width) - (r.x + r.width);
      const db = (b.y + b.height) - (r.y + r.height);
      if (dr > 0.5) issues.push('DERECHA +' + dr.toFixed(1));
      if (db > 0.5) issues.push('ABAJO +' + db.toFixed(1));
      if (b.x < r.x - 0.5) issues.push('IZQUIERDA ' + (r.x - b.x).toFixed(1));
      if (b.y < r.y - 0.5) issues.push('ARRIBA ' + (r.y - b.y).toFixed(1));
      if (best.area > canvasArea * 0.85) issues.push('FUERA-DE-PANEL');
    }
    if (b.x + b.width > vb.x + vb.width + 0.5) issues.push('FUERA-CANVAS');
    if (b.y + b.height > vb.y + vb.height + 0.5) issues.push('FUERA-CANVAS-ABAJO');
    if (issues.length) {
      out.push({svg: name, texto: (t.textContent || '').trim().slice(0, 60),
                issues: issues.join(' | '), fs: getComputedStyle(t).fontSize});
    }
  }
}
const pre = document.createElement('pre');
pre.id = 'RESULT';
pre.textContent = JSON.stringify(out);
document.body.appendChild(pre);
"""


def main():
    fallos = 0
    for svg in sorted(IMG.glob("*.svg")):
        # 1) XML bien formado (el parser del navegador es leniente y no lo detecta)
        try:
            xml.dom.minidom.parse(str(svg))
        except Exception as e:
            print(f"XML MAL FORMADO {svg.name}: {e}")
            fallos += 1
            continue

        content = svg.read_text(encoding="utf-8").replace("<svg ", f'<svg id="{svg.stem}" ', 1)
        html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"></head><body>{content}
<script>{JS}</script></body></html>"""
        with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False) as f:
            f.write(html)
            tmp = f.name
        res = subprocess.run(
            ["chromium", "--headless", "--disable-gpu", "--no-sandbox",
             "--virtual-time-budget=4000", "--dump-dom", f"file://{tmp}"],
            capture_output=True, text=True)
        pathlib.Path(tmp).unlink(missing_ok=True)
        m = re.search(r'<pre id="RESULT">(.*?)</pre>', res.stdout, re.S)
        if not m:
            print(f"!! no se pudo medir {svg.name}")
            continue
        data = json.loads(htmllib.unescape(m.group(1)))
        if not data:
            print(f"OK   {svg.name}")
            continue
        print(f"PROBLEMAS {svg.name}")
        for d in data:
            fallos += 1
            print(f"   fs={d['fs']:>6}  \"{d['texto']}\"")
            print(f"      -> {d['issues']}")
    print(f"\nDesbordes detectados: {fallos}")
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main())
