<div align="center">

# Auditoría de Seguridad — ACME Corp

**Máquina DockerLabs · objetivo `172.17.0.2`**

Dos banderas · dos vectores de escalada a root · ninguno requiere explotar
una vulnerabilidad de WordPress

[📄 Informe completo](AUDITORIA.md) · [🗂 Evidencia](evidence/) · [🖼 Diagramas](img/)

</div>

---

## Resumen

| | |
|---|---|
| **Objetivo** | `172.17.0.2` (DockerLabs / dockerlabs.es — «ACME Corp») |
| **Fecha** | 2026-10-17 |
| **Autor** | chifay |
| **Acceso inicial** | Credenciales filtradas en el banner SSH (pre-autenticación) |

### Banderas

| Nivel | Ubicación | Valor |
|---|---|---|
| Usuario | `/home/usuario/user.txt` | `FLAG{nmap_recon_ssh_foothold_7a9f24e1}` |
| Root | `/root/root.txt` | `FLAG{wp2shell_cve_2026_63030_core_rce_root_99d10c8b}` |

---

## Los dos vectores de escalada

| Vector | Descripción | Esfuerzo | Remediación |
|---|---|---|---|
| **A — SUID** | `/usr/bin/bash` y `/usr/bin/dash` con bit setuid root (`4755`); `bash -p` conserva el euid | **1 comando** | `chmod u-s` |
| **B — WordPress** | `wp-content/` en `777` + pool de PHP-FPM con `user = root` | 2 cambios de config | `user = www-data` + socket Unix |

![Cadena de ataque](img/01-kill-chain.png)

**Conclusión principal:** el Vector A es una escalada trivial y evitable con un
único `chmod`. Además, **parchear las CVE de WordPress no cerraría el Vector
B**, porque se trata de una mala configuración de permisos y no de código
vulnerable.

![Mecanismo SUID](img/02-suid-mechanism.png)

![Comparación de vectores](img/03-two-vectors.png)

---

## Hallazgos principales

| # | Hallazgo | Severidad | Vector |
|---|---|---|---|
| 1 | `/usr/bin/bash` y `/usr/bin/dash` con bit SUID root (`4755`) | **Crítica** | A |
| 2 | Credenciales de producción en el banner SSH, previo a autenticación | **Crítica** | — |
| 3 | `wp-content/` con permisos `777` → escritura de PHP por cualquier usuario | **Crítica** | B |
| 4 | Pool de PHP-FPM con `user = root` → ejecución de PHP como root | **Crítica** | B |
| 5 | Servicios internos (WP `:8080`, FPM `:9000`) en loopback, accesibles desde cualquier shell | Alta | B |
| 6 | WordPress Core reintroducido a versión vulnerable (CVE-2026-60137 / CVE-2026-63030) | Alta | — |
| 7 | Credenciales de BD en `wp-config.php` legible (`0644`) | Media | B |
| 8 | `DISALLOW_FILE_MODS=false` y `FS_METHOD=direct` permiten instalar código vía panel | Media | B |
| 9 | Contraseña de usuario débil y publicada en un banner | Media | — |

El detalle completo, con comandos y salidas, está en **[`AUDITORIA.md`](AUDITORIA.md)**.

---

## Fases

| Fase | Contenido | Diagrama |
|---|---|---|
| 1 | Reconocimiento de puertos (2 de 65535 abiertos) | [img/05](img/05-nmap-scan.png) |
| 2 | Credenciales filtradas en el banner SSH | [img/04](img/04-phases-recon.png) |
| 3 | Acceso y bandera de usuario | — |
| 4 | Enumeración: SUID, pool de FPM, vhosts, permisos | — |
| 5 | **Vector A** — escalada por `bash -p` | — |
| 6 | **Vector B** — escalada por WordPress + FPM | — |

---

## Estructura del repositorio

```
.
├── README.md              este documento
├── AUDITORIA.md           informe completo de la auditoría
├── LICENSE                MIT
├── img/                   5 diagramas (SVG editable + PNG)
├── evidence/              14 capturas de evidencia, con SHA256SUMS
│   ├── 01-recon/
│   ├── 02-initial-access/
│   ├── 03-enumeration/
│   ├── 04-vector-a-suid/
│   ├── 05-vector-b-wordpress/
│   └── 06-cleanup/
├── tools/                 scripts de trabajo
│   ├── capture_evidence.sh    regenera toda la evidencia
│   ├── rsh.example.sh         helper SSH (usa ACME_SSH_PASS)
│   ├── fcgi_pwn.py            cliente FastCGI (vía no utilizada)
│   ├── check_clearance.py     verificador de texto en los SVG
│   └── check_orphan.py        verificador de texto fuera de panel
└── inputs/                ficheros aportados por el laboratorio
```

---

## Reproducir

El laboratorio se despliega aparte (la imagen `acme.tar` no se versiona):

```bash
./auto_deploy.sh acme.tar     # el script original de DockerLabs
```

Una vez el contenedor esté en marcha, regenerar la evidencia completa:

```bash
export ACME_SSH_PASS='<credencial del banner SSH>'
./tools/capture_evidence.sh
```

Verificar la integridad de la evidencia:

```bash
cd evidence && sha256sum -c SHA256SUMS
```

---

## Notas de manejo

- **El Vector A no deja artefactos** en el objetivo: solo ejecuta comandos.
  El Vector B sí requiere escribir un `.php`, que se elimina al terminar; la
  prueba está en `evidence/06-cleanup/`.
- `/usr/bin/bash` conserva su bit SUID **de forma deliberada**: es el
  hallazgo auditado, no un residuo.
- `evidence/` incluye la credencial en `02-initial-access/` porque **es la
  prueba** del hallazgo. Si este material se comparte fuera del ámbito del
  laboratorio, revisa ese fichero.

---

<div align="center">

*Auditoría de seguridad — DockerLabs / dockerlabs.es · laboratorio de*
*entrenamiento con fines educativos.*

</div>
