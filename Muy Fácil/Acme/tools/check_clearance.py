#!/usr/bin/env python3
"""Informe de holgura: texto que cruza el recuadro o que queda pegado a su borde."""
import html as htmllib
import json
import pathlib
import re
import subprocess
import tempfile

IMG = pathlib.Path(__file__).resolve().parent.parent / "img"
UMBRAL = 3.0

JS = r"""
const out = [];
for (const svg of document.querySelectorAll('svg')) {
  const name = svg.id;
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
    const r = best.b;
    const clr = {
      der: (r.x + r.width) - (b.x + b.width),
      aba: (r.y + r.height) - (b.y + b.height),
      izq: b.x - r.x,
      arr: b.y - r.y
    };
    const min = Math.min(clr.der, clr.aba, clr.izq, clr.arr);
    out.push({
      svg: name,
      texto: (t.textContent || '').trim().slice(0, 56),
      min: +min.toFixed(1),
      clr: `der=${clr.der.toFixed(1)} aba=${clr.aba.toFixed(1)} izq=${clr.izq.toFixed(1)} arr=${clr.arr.toFixed(1)}`,
      rect: [r.x.toFixed(0), r.y.toFixed(0), r.width.toFixed(0), r.height.toFixed(0)].join(','),
      fs: getComputedStyle(t).fontSize
    });
  }
}
const pre = document.createElement('pre');
pre.id = 'RESULT';
pre.textContent = JSON.stringify(out);
document.body.appendChild(pre);
"""

rows = []
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
    rows.extend(json.loads(htmllib.unescape(m.group(1))))

print(f"{'SVG':<24} {'min':>6}  {'fs':>7}  texto")
print("-" * 110)
problemas = 0
for r in sorted(rows, key=lambda x: x["min"]):
    if r["min"] < UMBRAL:
        problemas += 1
        flag = "CRUZA" if r["min"] < 0 else "pegado"
        print(f"{r['svg']:<24} {r['min']:>6.1f}  {r['fs']:>7}  [{flag}] \"{r['texto']}\"")
        print(f"{'':<24} {'':>6}  {'':>7}  {r['clr']}  rect[{r['rect']}]")
print("-" * 110)
print(f"Total textos: {len(rows)}   Con holgura < {UMBRAL}px: {problemas}")
