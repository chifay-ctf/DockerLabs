#!/bin/bash
# Vigilante: espera a que la fuerza bruta encuentre la credencial y, en cuanto
# aparece, ejecuta automaticamente la captura de evidencia y la escalada.
set -u
cd "$(dirname "$0")/.." || exit 1

LOG="${1:-/tmp/opencode/brute_master.log}"
EVIDENCE_DIR=evidence

echo "[*] vigilando $LOG ..."
while true; do
    if grep -q 'CREDENCIAL ENCONTRADA' "$LOG" 2>/dev/null; then
        USER_FOUND=$(grep -oE 'CREDENCIAL ENCONTRADA: [^ ]+' "$LOG" | head -1 | awk '{print $3}')
        PASS_FOUND=$(grep -oE 'CREDENCIAL ENCONTRADA: .*' "$LOG" | head -1 | awk '{print $4}')
        echo "[+] CREDENCIAL: $USER_FOUND / $PASS_FOUND"
        export HH_USER="$USER_FOUND"
        export HH_PASS="$PASS_FOUND"
        echo "[*] ejecutando captura de evidencia..."
        python3 tools/capture_evidence.py
        echo "[*] captura terminada"
        exit 0
    fi
    if grep -q 'Sin exito' "$LOG" 2>/dev/null; then
        echo "[-] la fuerza bruta termino sin exito"
        exit 1
    fi
    sleep 15
done
