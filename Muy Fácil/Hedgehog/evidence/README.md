# Evidencia — Hedgehog

Capturas tomadas contra `172.17.0.2` durante la auditoría del 2026-10-19.
Cada fichero incluye, cuando aplica, el comando ejecutado y su salida.

| Ruta | Contenido |
|---|---|
| `01-reconocimiento/nmap-completo.txt` | `nmap -p- -sV -sC`: 22/tcp OpenSSH 9.6p1, 80/tcp Apache 2.4.58. |
| `01-reconocimiento/nmap-tcp-completo.txt` | Escaneo inicial de puertos y scripts. |
| `01-reconocimiento/nmap-udp.txt` | UDP top-10: sin servicios relevantes. |
| `01-reconocimiento/barrido-red.txt` | `nmap -sn 172.17.0.0/24`: solo el objetivo. |
| `02-servicio-web/index-http.txt` | Respuesta HTTP completa de `index.html`. |
| `02-servicio-web/index-hex.txt` | Cuerpo en hexadecimal: `tails\n` (6 bytes). |
| `02-servicio-web/enumeracion-gobuster.txt` | Fuerza bruta de rutas: solo `index.html` y 403 de `.ht*`. |
| `02-servicio-web/pista-web.txt` | Análisis de la pista y descartes de contenido. |
| `03-fuerza-bruta/defensas-ssh.txt` | Retardo por fallo, MaxAuthTries y tasa real por número de hilos. |
| `03-fuerza-bruta/credencial-hallada.txt` | Posición de la contraseña en rockyou y ataque dirigido a la cola. |
| `03-fuerza-bruta/posicion-en-rockyou.txt` | Línea exacta y posición en la lista invertida. |
| `03-fuerza-bruta/diccionarios-probados.txt` | Bloques de candidatos probados y cobertura total. |
| `04-acceso-inicial/tails.txt` | `id`, `hostname`, `sudo -l` y home de `tails`. |
| `04-acceso-inicial/home-tails.txt` | Permisos y contenido del home de `tails`. |
| `04-acceso-inicial/sudo-rules-tails.txt` | Regla `(sonic) NOPASSWD: ALL`. |
| `05-movimiento-lateral/sonic.txt` | `sudo -u sonic`, `sudo -l` y lectura de `Documentos/contraseña`. |
| `05-movimiento-lateral/sudo-rules-sonic.txt` | Regla `(ALL) NOPASSWD: ALL`. |
| `06-escalada-root/root.txt` | `uid=0(root)`, sudoers, shadow y home de root. |
| `06-escalada-root/root-proof.txt` | Prueba de identidad efectiva y enumeración final. |
| `06-escalada-root/openssh-cve.txt` | Comprobación de CVE-2024-6387 en el paquete instalado. |
| `07-banderas/busqueda.txt` | Búsqueda exhaustiva de banderas: el laboratorio no incluye ninguna. |
| `99-historico/raw/` | Logs crudos de las sesiones SSH y del ataque. |

## Nota sobre las banderas

La búsqueda como `root` (uid 0) no encuentra `user.txt`, `root.txt`, `flag`,
`bandera` ni ningún fichero equivalente. Los únicos ficheros no estándar de
usuario son la configuración de shell y `/home/sonic/Documentos/contraseña`.
La prueba de compromiso es la identidad efectiva: `uid=1002(tails)` para el
acceso y `uid=0(root)` para la escalada.

## Integridad

`SHA256SUMS` cubre todos los ficheros de este directorio. Para verificarlo:

```sh
cd evidence && sha256sum -c SHA256SUMS
```
