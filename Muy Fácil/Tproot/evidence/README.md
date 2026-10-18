# Evidencia — Auditoría Tproot (CVE-2011-2523)

Evidencia capturada directamente del objetivo **172.17.0.2** el **2026-10-18**
(UTC), durante la auditoría descrita en `../AUDITORIA.md`.

Cada fichero lleva una cabecera con **fecha, objetivo, fase y comando
exacto**, seguida de la salida literal. No hay transcripciones manuales: todo
es la salida real de la ejecución.

Regenerable con `python3 ../tools/capture_evidence.py`.

---

## Estructura

| Ruta | Qué demuestra |
|---|---|
| `01-recon/nmap_full_scan.txt` | Escaneo de puertos: 21/tcp vsftpd 2.3.4, 80/tcp Apache 2.4.58 |
| `01-recon/ftp_banner.txt` | Banner `220 (vsFTPd 2.3.4)` y respuesta del servicio |
| `02-backdoor-trigger/trigger_sequence.txt` | Secuencia completa: USER → PASS → 6200 → shell root |
| `02-backdoor-trigger/trigger_matrix.txt` | 13 casos que aíslan la regla exacta del trigger |
| `03-root-shell/root_shell.txt` | `uid=0(root)`, hostname y versión del userland |
| `03-root-shell/root_flag.txt` | Contenido de `/root/root.txt` |
| `03-root-shell/single_use_behaviour.txt` | Prueba de que el backdoor solo admite un shell |
| `04-source-analysis/backdoor_commit.txt` | Commit `e084c95 "reapply infection"`, autor y fecha |
| `04-source-analysis/str_contains_space.txt` | La función con el chequeo del magic inyectado |
| `04-source-analysis/privops_call_site.txt` | `handle_login()` y las validaciones previas |
| `04-source-analysis/vsf_sysutil_extra.txt` | La función que abre el shell en el 6200 |
| `05-environment/vsftpd_build.txt` | Binario y árbol de compilación |
| `05-environment/processes.txt` | Procesos del contenedor y entrypoint |
| `05-environment/vsftpd_conf.txt` | Configuración activa de vsftpd |

## Bandera documentada

```
Root : 261fd3f32200f950f231816b4e9a0594   → /root/root.txt
```

No existe bandera de usuario en este laboratorio: el objetivo es precisamente
alcanzar `uid=0` sin autenticación válida.

## Integridad

`SHA256SUMS` contiene la huella de cada artefacto. Verificar con:

```bash
cd evidence && sha256sum -c SHA256SUMS
```

## Notas

- La auditoría fue de **solo lectura**: el backdoor no requiere escribir nada
  en el objetivo, solo abrir conexiones. No se modificó ningún fichero del
  contenedor.
- El único cambio de estado es el de los procesos (la sesión FTP y el shell
  del 6200), que se cierran al terminar la sesión.
- `evidence/` no contiene credenciales de usuario — el backdoor no las
  necesita — pero **sí el código fuente del backdoor y la bandera del
  laboratorio**, que son precisamente la prueba. Revísalo antes de compartirlo
  fuera del ámbito del laboratorio.
