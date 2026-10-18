<div align="center">

# Auditoría de Seguridad — Tproot

**DockerLabs · objetivo `172.17.0.2` · CVE-2011-2523**

Explotación del backdoor de **vsftpd 2.3.4** para obtener un shell root

[📄 Informe completo](AUDITORIA.md) · [🗂 Evidencia](evidence/) · [🖼 Diagramas](img/)

</div>

---

## Bandera

| Nivel | Ubicación | Valor |
|---|---|---|
| Root | `/root/root.txt` | `261fd3f32200f950f231816b4e9a0594` |

Única bandera del laboratorio: el objetivo es alcanzar `uid=0` **sin**
autenticación válida.

---

## Resumen

El objetivo expone un vsftpd 2.3.4 **compilado con la puerta trasera** de
2011. No hay credencial que buscar ni vulnerabilidad remota que explotar: el
backdoor está en el propio binario.

```
nmap → banner "220 (vsFTPd 2.3.4)" →
USER backdoor:) + PASS → el servidor abre 0.0.0.0:6200 →
nc 172.17.0.2 6200 → /bin/sh como uid=0(root) → /root/root.txt
```

![Cadena de ataque](img/01-kill-chain.png)

### Tres hallazgos más allá del exploit

1. **El árbol de fuentes infectado está dentro del contenedor** (`/tmp/vsftpd-2.3.4-infected`),
   con su repositorio git: el commit `e084c95 "reapply infection"` documenta la
   inyección línea a línea.
2. **El trigger exige un `PASS` además del `USER` malicioso**, y el usuario no
   puede empezar por `:`. Ningún exploit público documenta estas condiciones.
3. **Es de un solo uso**: `execl()` reemplaza la imagen del proceso, el bucle de
   `accept()` desaparece y el listener muere con el shell.

![Mecanismo del backdoor](img/02-backdoor-mechanism.png)

---

## Fases

| Fase | Contenido | Diagrama |
|---|---|---|
| 1 | Reconocimiento: 21/tcp vsftpd 2.3.4, 80/tcp Apache | — |
| 2 | Trigger: `USER backdoor:)` + `PASS` → abre el 6200 | [img/03](img/03-trigger-matrix.png) |
| 3 | Shell root (`uid=0`) y lectura de `/root/root.txt` | — |
| 4 | Análisis del código fuente infectado | [img/02](img/02-backdoor-mechanism.png) |
| 5 | El backdoor es de un solo uso | [img/04](img/04-single-use.png) |
| 6 | Entorno: procesos, binario y configuración | [img/05](img/05-infection-diff.png) |

---

## Hallazgos

| # | Hallazgo | Severidad |
|---|---|---|
| 1 | vsftpd 2.3.4 con backdoor compilado: ejecución remota de root sin autenticación | **Crítica** |
| 2 | El árbol de fuentes infectado y su repositorio git quedan en el contenedor | **Alta** |
| 3 | Configuración sin `seccomp_sandbox`: no se restringe la ejecución de `/bin/sh` | Alta |
| 4 | Configuración sin `chroot_local_user`: el shell root escribe en todo el sistema | Alta |
| 5 | `write_enable=YES` con `local_enable=YES`: escritura FTP con cuenta local | Media |
| 6 | El acceso anónimo falla con `500 OOPS` por `/var/ftp` inexistente | Baja |
| 7 | Apache 2.4.58 sirve la página por defecto de Ubuntu | Info |

El detalle completo está en **[`AUDITORIA.md`](AUDITORIA.md)**.

---

## Estructura

```
.
├── README.md              este documento
├── AUDITORIA.md           informe completo
├── LICENSE                MIT
├── img/                   5 diagramas (SVG editable + PNG)
├── evidence/              14 capturas de evidencia, con SHA256SUMS
│   ├── 01-recon/
│   ├── 02-backdoor-trigger/
│   ├── 03-root-shell/
│   ├── 04-source-analysis/
│   └── 05-environment/
└── tools/
    ├── vsftpd_backdoor.py    exploit: comando único o shell interactiva
    ├── bsh.py                ejecutor de comandos por el backdoor
    ├── capture_evidence.py   regenera toda la evidencia
    └── check_svg.py          verificador de XML y desbordes en los SVG
```

---

## Reproducir

El laboratorio se despliega aparte (la imagen `tproot.tar` no se versiona):

```bash
./auto_deploy.sh tproot.tar
```

Explotar:

```bash
python3 tools/vsftpd_backdoor.py -H 172.17.0.2 -c "id; cat /root/root.txt"
python3 tools/vsftpd_backdoor.py -H 172.17.0.2 -i     # shell interactiva
```

Regenerar la evidencia y verificar su integridad:

```bash
python3 tools/capture_evidence.py
cd evidence && sha256sum -c SHA256SUMS
```

---

## Notas

- El exploit **no necesita credenciales**: el backdoor se arma con un `USER`
  malicioso y un `PASS` cualquiera.
- La sesión FTP **debe permanecer abierta** mientras se usa el shell del 6200.
- Un trigger entrega **un** shell. Si se cierra, hay que volver a dispararlo.
- La auditoría fue de **solo lectura** sobre el contenedor: no se modificó
  ningún fichero del objetivo.
- ⚠️ `tools/` contiene herramientas que dan acceso root sin credenciales.
  `evidence/` incluye el código fuente del backdoor y la bandera del
  laboratorio: revísalo antes de compartirlo fuera del ámbito del laboratorio.

---

<div align="center">

*Auditoría de seguridad — DockerLabs / dockerlabs.es · laboratorio de*
*entrenamiento con fines educativos.*

</div>
