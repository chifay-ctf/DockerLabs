#!/usr/bin/env python3
"""
Genera de forma DETERMINISTA todas las listas de candidatos de la auditoría.

Todo se escribe en wordlists/ (dentro del directorio de trabajo) para que las
listas sobrevivan a un reinicio del equipo, y no en /tmp.

Fuentes, todas de caja negra:
  - La web publica "tails"  -> usuario objetivo.
  - "Hedgehog" / Sonic      -> temática Sega para las variantes.
  - dockerlabs.es es una plataforma en español -> diccionario es y diminutivos.
  - Estilo del autor        -> patrón año + símbolo + CTF (visto en Acme).
  - Listas públicas         -> xato-net-10M, rockyou, nmap.lst, john.lst.
"""
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
W = ROOT / "wordlists"
W.mkdir(exist_ok=True)

ROCKYOU = "/usr/share/wordlists/rockyou.txt"
XATO100K = "/usr/share/seclists/Passwords/Common-Credentials/xato-net-10-million-passwords-100000.txt"
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


def gen_author_style():
    """Contraseñas que siguen el patrón del autor: base + año + símbolo + CTF."""
    bases = ["tails","Tails","TAILS","sonic","Sonic","hedgehog","Hedgehog","erizo","zorro",
             "miles","prower","sega","Sega","dockerlabs","DockerLabs","docker","ubuntu",
             "password","Password","P@ssw0rd","p@ssw0rd","P@ssword","admin","root","usuario"]
    nums = ["","1","12","123","1234","12345","01","007","99"]
    years = ["2020","2021","2022","2023","2024","2025","2026"]
    syms = ["","!","!!","!!!","@","#","$","*",".","-_","_","!@#","@2024","@2025","@2026"]
    combos = ["_CTF!","_CTF","-CTF!","CTF!","CTF","_ctf!","_2024!","_2025!","_2026!",
              "2024!","2025!","2026!"]
    out, seen = [], set()

    def add(w):
        if w and w not in seen:
            seen.add(w)
            out.append(w)

    for b in bases:
        for y in years:
            for t in combos:
                add(b + y + t)
                add(b + "_" + y + t)
                add(b + "-" + y + t)
        for n in nums:
            for s in syms:
                add(b + n + s)
            for y in years:
                add(b + n + y)
                add(b + n + y + "!")
    for b in ["tails","Tails","sonic","Sonic","hedgehog","Hedgehog"]:
        add(b.lower() + "@" + b.capitalize())
        add(b.capitalize() + "2024"); add(b.capitalize() + "2026")
        add(b + "2024!"); add(b + "2026!"); add(b + "2025!")
        add(b.capitalize() + "@2024"); add(b.capitalize() + "@2026")
    return out


def gen_lore():
    """Referencias del universo Sonic no cubiertas por la lista temática."""
    lore = ["greenhill","greenhillzone","chemicalplant","chemical","starlight","casinonight",
            "casino","mobius","mobius1","angelisland","emeraldhill","soniccd","sonicmania",
            "mania","chaosemerald","masteremerald","goldring","rings","ring","spinball",
            "hydrocity","marblezone","springyard","labyrinthzone","scrapbrain","metropolis",
            "oceanpalace","mysticruins","stationsquare","westsideisland",
            "eggcarrier","deathegg","sonicteam","teamchaotix","freedomfighters",
            "satam","aosth","sonicunderground","underground","sonicboom","sonicprime",
            "shadowthehedgehog","teamdark","teamrose","babylon","rogues","eggmanland"]
    sfx = ["","1","12","123","1234","!","!!","@","#","2024","2025","2026","01"]
    out, seen = [], set()

    def add(w):
        if w and w not in seen:
            seen.add(w)
            out.append(w)

    for b in lore:
        for s in sfx:
            add(b + s); add(b.capitalize() + s); add(b.upper() + s)
    return out


def gen_dims():
    """Diminutivos y términos afectivos en español, con sufijos.

    El diccionario ispell no incluye diminutivos, que son una forma muy común
    de contraseña en español. Se generan aquí a partir de sustantivos cortos.
    """
    nouns = """perro gato osito conejo pollo pato caballo raton rata pajaro pez tortuga loro
hamster cobaya lobo zorro erizo ardilla mono tigre leon delfin ballena casa amor vida sol luna flor
cielo mar corazon nina nino mama papa abuela abuelo tia tio hermana hermano amiga amigo bebe reina
rey princesa principe angel estrella mundo fuego agua tierra viento noche dia manana tarde verano
invierno primavera playa monte campo ciudad coche moto puerta ventana mesa silla libro telefono musica
cancion baile fiesta alegria tesoro dinero oro plata diamante perla rosa margarita girasol clavel
tulipan mariposa bruja hada duende caramelo chocolate fresa platano manzana naranja limon sandia melon
uva cereza pan dulce tarta pastel galleta leche cafe vino cerveza""".split()
    nouns = sorted(set(nouns))
    vow = set("aeiouáéíóú")
    out, seen = [], set()

    def add(w):
        if w and w not in seen:
            seen.add(w)
            out.append(w)

    def base_of(w):
        return w[:-1] if w and w[-1] in vow else w

    for suf in ("","1","123","!","2024","12","!!","1234","2025","2026"):
        for n in nouns:
            b = base_of(n)
            for d in ("ito","ita","itos","itas"):
                add(b + d + suf); add((b + d + suf).capitalize())
    for suf in ("","1","123","!","2024"):
        for n in nouns:
            b = base_of(n)
            for d in ("cito","cita","citos","citas"):
                add(b + d + suf); add((b + d + suf).capitalize())
    for suf in ("","1","123","!","2024"):
        for pre in ("mi","el","la","linda","lindo"):
            for n in nouns:
                add(pre + n + suf); add(pre.capitalize() + n.capitalize() + suf)
    return out


def main():
    rock = read(ROCKYOU)
    xato = read(XATO100K)

    author = gen_author_style()
    (W / "passwords_author.txt").write_text("\n".join(author) + "\n", encoding="utf-8")
    print(f"author_style  : {len(author):>8}")

    # fallback = estilo del autor + lore + xato[3613:] + rockyou[44704:150000]
    fb, seen = [], set()

    def add(w):
        w = w.strip()
        if w and w not in seen:
            seen.add(w)
            fb.append(w)

    for w in author:
        add(w)
    lore = gen_lore()
    for w in lore:
        add(w)
    for w in xato[3613:100000]:
        add(w)
    for w in rock[44704:150000]:
        add(w)
    (W / "passwords_fallback.txt").write_text("\n".join(fb) + "\n", encoding="utf-8")
    print(f"fallback      : {len(fb):>8}")

    dims = gen_dims()
    (W / "passwords_dims.txt").write_text("\n".join(dims) + "\n", encoding="utf-8")
    print(f"diminutivos   : {len(dims):>8}")

    # combinada: diminutivos primero, luego el resto del fallback
    comb, seen2 = [], set()

    def add2(w):
        w = w.strip()
        if w and w not in seen2:
            seen2.add(w)
            comb.append(w)

    for w in dims:
        add2(w)
    for w in fb:
        add2(w)
    (W / "passwords_combined.txt").write_text("\n".join(comb) + "\n", encoding="utf-8")
    print(f"combinada     : {len(comb):>8}")

    # reanudacion desde la ultima posicion conocida
    last = 31548
    if len(comb) > last:
        tail = comb[last:]
        (W / "passwords_resume.txt").write_text("\n".join(tail) + "\n", encoding="utf-8")
        print(f"resume (>{last}): {len(tail):>8}")


if __name__ == "__main__":
    main()
