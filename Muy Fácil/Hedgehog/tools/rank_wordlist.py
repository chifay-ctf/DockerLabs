#!/usr/bin/env python3
"""
Reordena la wordlist por probabilidad de acierto.

Corrige el orden del listado anterior: rockyou esta ordenado por frecuencia
de roast y sus entradas mas altas ("123456", "password", "qwerty") ya estan
cubiertas, pero a partir de la posicion ~3.000 contiene contrasenas que una
persona elige de verdad. xato-10M es muy solapado con rockyou, asi que se
coloca despues.

Orden final:
  1. tematica ampliada (Sega/Sonic: casos, camelCase, leet, sufijos)
  2. rockyou 3k-50k        <- nuevo, alta probabilidad
  3. xato-net-10M top 100k
  4. nmap.lst + john.lst   <- especificas de SSH
  5. rockyou 50k-100k
  6. diccionario espanol
  7. rockyou 100k-150k
"""
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
W = ROOT / "wordlists"
OUT = W / "passwords_ranked.txt"

ROCKYOU = "/usr/share/wordlists/rockyou.txt"
XATO = "/usr/share/seclists/Passwords/Common-Credentials/xato-net-10-million-passwords-100000.txt"
SPANISH = "/usr/share/spiderfoot/spiderfoot/dicts/ispell/spanish.dict"


def read(path, limit=None):
    try:
        out = []
        with open(path, encoding="utf-8", errors="ignore") as fh:
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

    # 1) tematica ampliada
    for w in read(W / "passwords_theme.txt"):
        add(w)

    rock = read(ROCKYOU)

    # 2) rockyou 3k-50k
    for w in rock[3000:50000]:
        add(w)

    # 3) xato top 100k
    for w in read(XATO):
        add(w)

    # 4) nmap.lst + john.lst
    for w in read("/usr/share/wordlists/nmap.lst"):
        add(w)
    for w in read("/usr/share/wordlists/john.lst"):
        add(w)

    # 5) rockyou 50k-100k
    for w in rock[50000:100000]:
        add(w)

    # 6) espanol
    for w in read(SPANISH):
        add(w.lower())

    # 7) rockyou 100k-150k
    for w in rock[100000:150000]:
        add(w)

    OUT.write_text("\n".join(words) + "\n", encoding="utf-8")
    marks = {}
    for probe in ("tails", "123456", "password", "zorro", "qwerty"):
        for i, w in enumerate(words):
            if w == probe:
                marks[probe] = i
                break
    print(f"total -> {OUT} ({len(words)})")
    print("posiciones de referencia:", marks)


if __name__ == "__main__":
    main()
