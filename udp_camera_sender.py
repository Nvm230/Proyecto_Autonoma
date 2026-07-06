"""
Ejecutar en la Raspberry Pi:
    python3 udp_camera_sender.py

Captura la camara, comprime a JPEG y envia por UDP a la laptop.
"""
import cv2
import socket
import struct
import time
import sys

# ---- CONFIGURACION ----
LAPTOP_IP = '192.168.10.101'  # IP de la laptop en wlan1 (confirmada)
PORT = 5600
JPEG_QUALITY = 80  # 0-100
WIDTH = 640
HEIGHT = 480
FPS = 15
# -----------------------

def main():
    cap = cv2.VideoCapture(0, cv2.CAP_V4L2)  # Forzar V4L2, evitar GStreamer
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)
    cap.set(cv2.CAP_PROP_FPS, FPS)

    if not cap.isOpened():
        print("[ERROR] No se pudo abrir la camara /dev/video0")
        sys.exit(1)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    interval = 1.0 / FPS

    print(f"[OK] Enviando video {WIDTH}x{HEIGHT} a {LAPTOP_IP}:{PORT} @ {FPS} FPS...")
    print("[   ] Presiona Ctrl+C para detener.")

    frame_count = 0
    while True:
        start = time.time()
        ret, frame = cap.read()
        if not ret:
            print("[WARN] No se pudo leer el frame, reintentando...")
            continue

        # Comprimir a JPEG (mucho mas liviano que RGB crudo)
        encode_params = [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY]
        _, buffer = cv2.imencode('.jpg', frame, encode_params)
        jpg_bytes = buffer.tobytes()

        # Prefijo de 4 bytes con el tamano del frame
        header = struct.pack('>I', len(jpg_bytes))
        packet = header + jpg_bytes

        # Un JPEG 640x480 al 80% pesa ~20-40KB, cabe en un datagrama UDP
        if len(packet) > 65507:
            print(f"[WARN] Frame muy grande ({len(packet)} bytes), bajando calidad...")
            continue

        sock.sendto(packet, (LAPTOP_IP, PORT))
        frame_count += 1
        if frame_count % FPS == 0:
            print(f"[{frame_count}] Enviado frame de {len(jpg_bytes)/1024:.1f} KB")

        # Mantener el FPS objetivo
        elapsed = time.time() - start
        sleep_time = interval - elapsed
        if sleep_time > 0:
            time.sleep(sleep_time)

if __name__ == '__main__':
    main()
