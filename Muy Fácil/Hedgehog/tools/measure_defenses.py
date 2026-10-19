#!/usr/bin/env python3
"""
Mide y documenta las defensas del servidor SSH del laboratorio.

Tres mediciones independientes, todas reproducibles:

  1. Retardo por autenticacion fallida (pam_fail_delay).
     Separa el coste del handshake del coste del intento fallido.

  2. MaxAuthTries: cuantos intentos acepta una misma conexion antes de
     cerrarla.

  3. Tasa practica de fuerza bruta con distinto numero de hilos, para
     localizar el punto donde MaxStartups empieza a cortar conexiones.

Uso:  python3 tools/measure_defenses.py
"""
import logging
import socket
import threading
import time

import paramiko

HOST = "172.17.0.2"
PORT = 22
USER = "tails"

logging.getLogger("paramiko").setLevel(logging.CRITICAL)
paramiko.util.log_to_file("/dev/null", level=logging.CRITICAL)


def connect():
    """TCP + handshake SSH. Devuelve (transporte, segundos_de_handshake)."""
    t0 = time.time()
    sock = socket.create_connection((HOST, PORT), timeout=15)
    tcp = time.time() - t0
    transport = paramiko.Transport(sock)
    transport.start_client(timeout=20)
    return transport, tcp, time.time() - t0 - tcp


def medir_retardo(n=5):
    print(f"--- Retardo por fallo: {n} muestras secuenciales (usuario {USER}) ---")
    for i in range(1, n + 1):
        try:
            transport, tcp, kex = connect()
        except Exception as exc:
            print(f"  intento {i}: fallo de conexion: {exc}")
            continue
        t1 = time.time()
        try:
            transport.auth_password(USER, f"sondeo-{i}")
            resultado = "ACEPTADO"
        except paramiko.AuthenticationException:
            resultado = "denegado"
        finally:
            auth = time.time() - t1
            try:
                transport.close()
            except Exception:
                pass
        print(f"  intento {i}: tcp={tcp:.3f}s  kex={kex:.3f}s  auth={auth:.3f}s -> {resultado}")
        time.sleep(0.5)


def medir_maxauthtries(n=8):
    print(f"--- MaxAuthTries: hasta {n} intentos sobre UNA sola conexion ---")
    try:
        transport, _, _ = connect()
    except Exception as exc:
        print(f"  no se pudo conectar: {exc}")
        return
    for i in range(1, n + 1):
        try:
            transport.auth_password(USER, f"sondeo-{i}")
            print(f"  intento {i}: ACEPTADO")
            break
        except paramiko.AuthenticationException:
            print(f"  intento {i}: denegado (la conexion sigue viva)")
        except Exception as exc:
            print(f"  intento {i}: {type(exc).__name__}: {str(exc)[:70]}")
            break
    try:
        transport.close()
    except Exception:
        pass


def medir_tasa(hilos, segundos):
    print(f"--- Tasa practica: {hilos} hilos durante {segundos} s ---")
    parada = threading.Event()
    contador = [0]
    cerrojo = threading.Lock()

    def trabajador():
        while not parada.is_set():
            try:
                transport, _, _ = connect()
            except Exception:
                continue
            for _ in range(6):  # MaxAuthTries
                if parada.is_set():
                    break
                try:
                    transport.auth_password(USER, "x")
                except paramiko.AuthenticationException:
                    with cerrojo:
                        contador[0] += 1
                except Exception:
                    break
            try:
                transport.close()
            except Exception:
                pass

    hilos_objeto = [threading.Thread(target=trabajador, daemon=True) for _ in range(hilos)]
    t0 = time.time()
    for h in hilos_objeto:
        h.start()
    time.sleep(segundos)
    parada.set()
    for h in hilos_objeto:
        h.join(timeout=15)
    transcurrido = time.time() - t0
    intentos = contador[0]
    print(f"  intentos={intentos}  tiempo={transcurrido:.1f}s  tasa={intentos / transcurrido:.1f} intentos/s")
    time.sleep(3)


if __name__ == "__main__":
    print("=== MEDICION DE DEFENSAS SSH — 172.17.0.2 ===")
    print(f"=== fecha: {time.strftime('%Y-%m-%d %H:%M:%S')} ===\n")
    medir_retardo()
    print()
    medir_maxauthtries()
    print()
    medir_tasa(40, 30)
    medir_tasa(80, 30)
    print()
    medir_retardo(n=3)
    print("\n=== fin ===")
