#!/usr/bin/env python3
"""
Lista definitiva de contrasenas para Hedgehog, ordenada por probabilidad real.

FUENTE (solo caja negra):
  - La web (:80) publica "tails"  =>  usuario a atacar.
  - "Hedgehog" / Sonic  =>  tematica Sega para las variantes.
  - dockerlabs.es es una plataforma en espanol  =>  diccionario es.
  - Listas de contrasenas reales ordenadas por frecuencia (xato-net 10M).

Orden de ataque (de mas a menos probable):
  1. tematica (Sega/Sonic + usuarios)
  2. xato-net-10M top 100k  (frecuencia real de senales)
  3. nmap.lst + john.lst    (especificas de SSH)
  4. rockyou top 30k
  5. diccionario espanol
  6. rockyou resto
"""
import pathlib

OUT = pathlib.Path(__file__).resolve().parent.parent / "wordlists"
OUT.mkdir(parents=True, exist_ok=True)

ROCKYOU = "/usr/share/wordlists/rockyou.txt"
XATO = "/usr/share/seclists/Passwords/Common-Credentials/xato-net-10-million-passwords-100000.txt"
SPANISH = "/usr/share/spiderfoot/spiderfoot/dicts/ispell/spanish.dict"
NMAP_L = "/usr/share/wordlists/nmap.lst"
JOHN_L = "/usr/share/wordlists/john.lst"

TERMS = [
    "tails", "hedgehog", "sonic", "knuckles", "shadow", "silver", "amy",
    "rouge", "chao", "omochao", "tikal", "biolizard", "eggman",
    "drrobotnik", "robotnik", "sega", "gamegear", "megadrive", "genesis",
    "emerald", "chaos", "master", "supersonic", "darksonic", "teamsonic",
    "sonictails", "tailssonic", "hedge", "zorro", "zorros", "colmillo",
    "colita", "colas", "miles", "bigthecat", "orbot", "gamma", "beta",
    "mario", "luigi", "peach", "yoshi", "zelda", "kratos", "minecraft",
    "pikachu", "naruto", "goku", "vegeta", "pokemon", "digimon", "ragnarok",
]
SUFFIXES = ["", "1", "12", "123", "1234", "12345", "!", "!!", "@", "#",
            "2024", "2025", "2026", "01", "007", "99", "666", "777", "_"]
CASES = [str.lower, str.upper, str.capitalize, str.title]


def read(path, limit=None):
    try:
        with open(path, encoding="utf-8", errors="ignore") as fh:
            out = []
            for i, line in enumerate(fh):
                if limit is not None and i >= limit:
                    break
                out.append(line.strip())
            return out
    except OSError:
        return []


def main():
    words, seen = [], set()

    def add(w):
        w = w.strip()
        if w and w not in seen:
            seen.add(w)
            words.append(w)

    # 1) tematica
    for t in TERMS:
        for c in CASES:
            b = c(t)
            for s in SUFFIXES:
                add(b + s)

    # 2) xato 10M top 100k (frecuencia real)
    xato = read(XATO)
    for w in xato:
        add(w)

    # 3) wordlists de SSH
    for w in read(NMAP_L):
        add(w)
    for w in read(JOHN_L):
        add(w)

    # 4) rockyou top 50k
    rock = read(ROCKYOU)
    for w in rock[:50000]:
        add(w)

    # 5) espanol
    for w in read(SPANISH):
        add(w.lower())

    # 6) rockyou 50k-150k
    for w in rock[50000:150000]:
        add(w)

    (OUT / "passwords_final.txt").write_text("\n".join(words) + "\n", encoding="utf-8")
    print(f"total -> {OUT / 'passwords_final.txt'} ({len(words)})")
    # puntos de corte para monitorizar
    marks = {}
    for probe in ("tails", "123456", "zorro", "password", "qwerty", "dragon"):
        for i, w in enumerate(words):
            if w == probe:
                marks[probe] = i
                break
    print("posiciones de referencia:", marks)


if __name__ == "__main__":
    main()
