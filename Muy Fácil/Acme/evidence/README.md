# Evidencia — Auditoría ACME Corp

Evidencia capturada directamente del objetivo **172.17.0.2** el
**2026-10-18** (UTC), durante la auditoría descrita en `../AUDITORIA.md`.

Cada fichero lleva una cabecera con **fecha, objetivo, fase y comando
exacto**, seguida de la salida literal. No hay transcripciones manuales:
todo es la salida real de la ejecución.

Regenerable con `../tools/capture_evidence.sh`.

---

## Estructura

| Ruta | Qué demuestra |
|---|---|
| `01-recon/nmap_full_scan.txt` | Escaneo de puertos: 2 de 65535 abiertos |
| `01-recon/nmap_full_scan_raw.txt` | Salida íntegra de nmap (sin reencuadrar) |
| `01-recon/http_maintenance_page.txt` | El puerto 80 solo sirve la página de mantenimiento |
| `01-recon/robots_and_migration_notes.txt` | `robots.txt` filtra `/migration_notes.txt` → remite a SSH |
| `02-initial-access/ssh_banner_preauth.txt` | **Banner SSH con credenciales emitido SIN autenticar** |
| `02-initial-access/user_flag.txt` | Identidad `uid=1000(usuario)` y bandera de usuario |
| `03-enumeration/suid_sgid_binaries.txt` | Lista SUID/SGID; `bash` y `dash` con bit setuid |
| `03-enumeration/php_fpm_pool_config.txt` | **Causa raíz del Vector B: pool FPM con `user = root`** |
| `03-enumeration/apache_vhosts.txt` | Vhost oculto de WordPress en `127.0.0.1:8080` |
| `03-enumeration/wp_content_permissions.txt` | `wp-content/` en `777` + servicios en loopback |
| `04-vector-a-suid/suid_bash_privilege_test.txt` | `bash -p` conserva el euid → `euid=0(root)` |
| `04-vector-a-suid/root_flag.txt` | Lectura de `/root/root.txt`, escritura en `/root`, lectura de `/etc/shadow` |
| `05-vector-b-wordpress/fpm_executes_as_root.txt` | Secuencia completa: escritura → petición HTTP → ejecución como root |
| `06-cleanup/cleanup_verification.txt` | Verificación de que no quedan artefactos en el objetivo |

## Banderas documentadas

```
Usuario : FLAG{nmap_recon_ssh_foothold_7a9f24e1}   → /home/usuario/user.txt
Root    : FLAG{wp2shell_cve_2026_63030_core_rce_root_99d10c8b} → /root/root.txt
```

## Integridad

`SHA256SUMS` contiene la huella de cada artefacto. Verificar con:

```bash
cd evidence && sha256sum -c SHA256SUMS
```

## Notas

- El Vector A (SUID) **no deja artefactos en el objetivo**: solo ejecuta
  comandos. El Vector B sí requiere escribir un `.php`, que se eliminó al
  terminar; la prueba está en `06-cleanup/`.
- El binario con bit SUID `/usr/bin/bash` se dejó **intacto de forma
  deliberada**: es el hallazgo auditado, no un residuo de la auditoría. El
  contenedor se destruye por completo con Ctrl+C en `auto_deploy.sh`.
- Las credenciales aparecen en las capturas porque **son la prueba** del
  hallazgo (fuga en el banner SSH). Si este material se comparte fuera del
  ámbito del laboratorio, revisa `02-initial-access/ssh_banner_preauth.txt`.
