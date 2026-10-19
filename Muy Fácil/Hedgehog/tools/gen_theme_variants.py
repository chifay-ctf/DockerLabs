#!/usr/bin/env python3
"""
Variantes tematicas ampliadas para Hedgehog.

Cubre formatos que la expansion basica no genera:
  - camelCase / PascalCase con mayusculas internas (HedgeHog, Tails123)
  - leet-speak (t41ls, s0nic, h3dg3h0g)
  - separadores y simbolos intercalados (tails-2024, tails@lab)
  - sufijos numericos y de temporada

Solo razonamiento de caja negra: la web publica "tails" y el lab se llama
"Hedgehog" (tematica Sega/Sonic).
"""
import pathlib
import sys

OUT = pathlib.Path(__file__).resolve().parent.parent / "wordlists"
OUT.mkdir(parents=True, exist_ok=True)

TERMS = [
    "tails", "hedgehog", "sonic", "knuckles", "shadow", "silver", "amy",
    "rouge", "chao", "omochao", "tikal", "eggman", "drrobotnik", "robotnik",
    "sega", "gamegear", "megadrive", "genesis", "emerald", "chaos",
    "supersonic", "darksonic", "teamsonic", "hedge", "zorro", "zorros",
    "colmillo", "colita", "miles", "mario", "luigi", "peach", "yoshi",
    "zelda", "kratos", "pikachu", "naruto", "goku", "vegeta", "pokemon",
    "digimon", "minecraft", "zelda", "sonia",
]

LEET = {"a": "4", "e": "3", "i": "1", "o": "0", "s": "5", "t": "7",
        "l": "1", "g": "9", "b": "8"}

SUFFIX = ["", "1", "12", "123", "1234", "!", "!!", "@", "#", "$", "2024",
          "2025", "2026", "01", "007", "99", "666", "777", "_", "-", "."]
SEPS = ["", "-", "_", ".", "@", "#", " "]


def camel(t):
    return t[0].upper() + t[1:]


def pascal(t):
    return "".join(w.capitalize() for w in t.replace("-", " ").split())


def leet(t):
    return "".join(LEET.get(ch, ch) for ch in t)


def main():
    words, seen = [], set()

    def add(w):
        if w and w not in seen:
            seen.add(w)
            words.append(w)

    forms = []
    for t in TERMS:
        forms += [t, t.upper(), t.capitalize(), t.title(), camel(t), pascal(t),
                  leet(t), leet(t).capitalize(), leet(t).upper()]
    for f in forms:
        for suf in SUFFIX:
            add(f + suf)
            for sep in SEPS:
                if sep:
                    add(f + sep + suf.lstrip("@#$") if suf else f + sep)

    # termino + separador + otro termino
    for a in ("tails", "hedgehog", "sonic"):
        for b in ("tails", "hedgehog", "sonic", "lab", "2024", "2026", "123"):
            for sep in SEPS:
                if sep:
                    add(a + sep + b)

    (OUT / "passwords_theme.txt").write_text("\n".join(words) + "\n", encoding="utf-8")
    print(f"tematicas ampliadas -> {OUT / 'passwords_theme.txt'} ({len(words)})")


if __name__ == "__main__":
    sys.exit(main())
