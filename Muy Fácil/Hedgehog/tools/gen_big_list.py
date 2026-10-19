#!/usr/bin/env python3
"""
Lista de contrasenas para la fuerza bruta de Hedgehog, ordenada por probabilidad.

FUENTE: solo razonamiento de caja negra.
  1. Pista de la web (:80) -> "tails"      => usuario.
  2. Nombre del lab "Hedgehog" -> tematica Sega/Sonic.
  3. La plataforma es dockerlabs.es (espanol) -> diccionario en espanol.
  4. Contrasenas triviles habituales.

Orden: tematica (mas probable) -> espanol -> rockyou.
"""
import pathlib

OUT = pathlib.Path(__file__).resolve().parent.parent / "wordlists"
OUT.mkdir(parents=True, exist_ok=True)

ROCKYOU = "/usr/share/wordlists/rockyou.txt"
SPANISH = "/usr/share/spiderfoot/spiderfoot/dicts/ispell/spanish.dict"

# ── 1. Terminos de la franchise Sega/Sonic ───────────────────────────────
TERMS = [
    "tails", "hedgehog", "sonic", "knuckles", "shadow", "silver", "amy",
    "rouge", "chao", "omochao", "tikal", "biolizard", "eggman",
    "drrobotnik", "robotnik", "sega", "gamegear", "megadrive", "genesis",
    "emerald", "chaos", "master", "supersonic", "darksonic", "teamsonic",
    "sonictails", "tailssonic", "shadowtails", "hedge", "zorro", "zorros",
    "colmillo", "colita", "colas", "miles", "mileseg", "amyrose",
    "bigthecat", "orbot", "gamma", "beta", "darkshadow", "darkamy",
    "jefe", "jefes", "doctor", "doctoreggman", "profesor",
]

# Sufijos que se prueban con cada termino
SUFFIXES = [
    "", "1", "12", "123", "1234", "12345", "!", "!!", "@", "#",
    "2024", "2025", "2026", "01", "007", "99", "666", "777",
]
CASE_FORMS = [str.lower, str.upper, str.capitalize, str.title]


def expand(terms):
    out = []
    for t in terms:
        for form in CASE_FORMS:
            base = form(t)
            for suf in SUFFIXES:
                out.append(base + suf)
    return out


def main():
    words, seen = [], set()

    def add(w):
        w = w.strip()
        if w and w not in seen:
            seen.add(w)
            words.append(w)

    # 1) tematica con patrones
    for w in expand(TERMS):
        add(w)

    # 2) rockyou: primero los mas comunes (10k) -> es lo que masprobablemente
    #    resuelve un lab. El resto se deja para el final.
    rock = []
    try:
        for i, l in enumerate(open(ROCKYOU, encoding="utf-8", errors="ignore")):
            if i >= 60000:
                break
            rock.append(l.strip())
    except OSError:
        pass
    for w in rock[:10000]:
        add(w)

    # 3) espanol: palabras del diccionario con sufijos comunes
    try:
        sp = [l.strip().lower() for l in open(SPANISH, encoding="utf-8", errors="ignore")]
    except OSError:
        sp = []
    for w in sp:
        add(w)
    for w in sp[:8000]:                      # sufijos solo sobre las mas comunes
        for suf in ("1", "!", "123"):
            add(w + suf)

    # 4) resto de rockyou
    for w in rock[10000:]:
        add(w)

    (OUT / "passwords_big.txt").write_text("\n".join(words) + "\n", encoding="utf-8")
    print(f"contrasenas -> {OUT / 'passwords_big.txt'} ({len(words)})")
    print(f"  tematica ~{len(expand(TERMS))}, espanol ~{len(sp)}, rockyou ~60000")
    print(f"\nprimeras 12: {words[:12]}")


if __name__ == "__main__":
    main()
