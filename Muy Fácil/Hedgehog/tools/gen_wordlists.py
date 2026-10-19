#!/usr/bin/env python3
"""
Genera las wordlists para la fuerza bruta del laboratorio Hedgehog.

FUENTE DE LA LISTA — solo razonamiento de caja negra, sin acceso al
contenedor:
  1. La pista del servidor web: "tails"  ->  nombre de usuario.
  2. El nombre del laboratorio: "Hedgehog"  ->  tematica Sega (SegaSonic).
     Personajes y conceptos de la franchise como base de contrasenas.
  3. Contrasenas triviales habituales en entornos de laboratorio.
  4. Patrones automaticos usuario==contrasena.

No se usa ninguna credencial obtenida de la imagen o del filesystem.
"""
import pathlib

OUT = pathlib.Path(__file__).resolve().parent.parent / "wordlists"
OUT.mkdir(parents=True, exist_ok=True)

# --- Usuarios: el primero es el que anuncia la web ---------------------
USERS = [
    "tails",                       # pista literal del servidor web (:80)
    "hedgehog",                    # nombre del laboratorio
    "sonic", "knuckles", "amy", "shadow", "silver", "rouge",
    "eggman", "drrobotnik", "chao", "tikal", "sega",
    "ubuntu", "root", "admin", "user", "guest", "test",
]

# --- Contrasenas tematicas (SegaSonic) ----------------------------------
THEME = [
    # el nombre de usuario y variantes
    "tails", "Tails", "TAILS", "tails123", "tails1234", "Tails123",
    "tails!", "tails1", "tails2024", "tails2026", "tailsies",
    "hedgehog", "Hedgehog", "hedgehog123", "hedgehog!",
    "sonic", "Sonic", "SONIC", "sonic123", "sonic!",
    "knuckles", "Knuckles", "amy", "Amy", "shadow", "Shadow",
    "silver", "Silver", "rouge", "Rouge", "chao", "Chao",
    "eggman", "Eggman", "drrobotnik", "DrRobotnik", "DrRobotnik!",
    "sega", "SEGA", "Sega", "gamegear", "megadrive", "genesis",
    # otros personajes / conceptos
    "tikal", "tikal123", "omochao", "biolizard", "dark sonic",
    "teamsonic", "sonicx", "sonic2", "tails2", "emerald",
    "chaos", "chaosemerald", "master", "robotnik", "egg",
    # combinaciones
    "sega123", "sega!", "sonictails", "tailssonic", "sonic&tails",
    "tails#1", "tails2023", "hedge", "hedge123",
]

# --- Contrasenas triviles habituales en labs -----------------------------
COMMON = [
    "password", "password1", "password123", "123456", "12345678",
    "1234567890", "123456789", "qwerty", "qwerty123", "letmein",
    "welcome", "monkey", "dragon", "iloveyou", "trustno1",
    "baseball", "football", "master", "sunshine", "princess",
    "abc123", "111111", "123123", "654321", "123321", "1234",
    "changeme", "default", "secret", "pass", "pass123", "pass1234",
    "toor", "root", "admin", "admin123", "administrator",
    "P@ssw0rd", "P@ssw0rd1", "p@ssw0rd", "Pa$$w0rd",
    "linux", "ubuntu", "kali", "test", "test123", "guest",
    "access", "hello", "welcome1", "login", "user", "user123",
]

# --- Patrones automaticos ----------------------------------------------
EXTRA = []
for u in USERS:
    EXTRA += [u, u + "1", u + "12", u + "123", u + "1234",
              u + "!", u + "!!", u + "2024", u + "2025", u + "2026",
              u.capitalize(), u.capitalize() + "1",
              u.capitalize() + "!", u.upper(), u + u]

# --- Ensamblado ---------------------------------------------------------
# Prioridad: lo tematico (mas probable en un lab con tematica) y despues
# lo trivial. Sin duplicados.
words, seen = [], set()
for group in (THEME, COMMON, EXTRA):
    for w in group:
        w = w.strip()
        if w and w not in seen:
            seen.add(w)
            words.append(w)

(OUT / "users.txt").write_text("\n".join(USERS) + "\n", encoding="utf-8")
(OUT / "passwords.txt").write_text("\n".join(words) + "\n", encoding="utf-8")

print(f"usuarios    -> {OUT / 'users.txt'}  ({len(USERS)})")
print(f"contrasenas -> {OUT / 'passwords.txt'} ({len(words)})")
print(f"\nPrimeros 15: {words[:15]}")
