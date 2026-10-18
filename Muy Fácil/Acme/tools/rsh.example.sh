#!/bin/bash
# -----------------------------------------------------------------------------
# Helper SSH — ejecutar un comando en el objetivo ACME Corp como «usuario».
#
# La credencial del laboratorio se obtiene del propio banner SSH del objetivo
# (véase evidence/02-initial-access/ssh_banner_preauth.txt). NO se versiona
# aquí: definela en la variable de entorno ACME_SSH_PASS antes de usar el
# script, o copia rsh.example.sh a rsh.sh y ajusta la línea de abajo.
#
#   export ACME_SSH_PASS='...'
#   ./tools/rsh.sh 'id'
# -----------------------------------------------------------------------------
set -u

TARGET="${ACME_TARGET:-172.17.0.2}"
USER="${ACME_USER:-usuario}"
PASS="${ACME_SSH_PASS:-}"

if [ -z "$PASS" ]; then
    echo "ERROR: define ACME_SSH_PASS (la credencial aparece en el banner SSH del objetivo)." >&2
    exit 1
fi

sshpass -p "$PASS" ssh \
    -o StrictHostKeyChecking=no \
    -o UserKnownHostsFile=/dev/null \
    -o LogLevel=ERROR \
    "$USER@$TARGET" "$@" 2>/dev/null
