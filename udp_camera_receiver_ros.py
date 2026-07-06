"""
Ejecutar en la Laptop (dentro de Distrobox):
    python3 udp_camera_receiver_ros.py

Recibe los frames JPEG por UDP desde la Raspberry Pi y los publica como
un topico ROS 2 /camera/image_raw, exactamente igual que usb_cam.
"""
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
import numpy as np
import socket
import struct
import threading

# ---- CONFIGURACION ----
LISTEN_PORT = 5600
PUBLISH_TOPIC = '/camera/image_raw'
# Correccion de exposicion: alpha < 1 oscurece, beta negativo baja brillo
# Ajusta ALPHA y BETA si la imagen se ve muy blanca o muy oscura
EXPOSURE_ALPHA = 1.0   # contraste (0.5 = muy oscuro, 1.0 = sin cambio)
EXPOSURE_BETA  = 0     # brillo adicional (-50 = muy oscuro, 0 = sin cambio)
# -----------------------

class UDPCameraReceiverNode(Node):
    def __init__(self):
        super().__init__('udp_camera_receiver')

        # Publicador de imagenes (identico a usb_cam)
        self.publisher = self.create_publisher(Image, PUBLISH_TOPIC, 1)
        self.bridge = CvBridge()

        self.latest_frame = None
        self.lock = threading.Lock()

        # Hilo separado para recibir UDP sin bloquear ROS
        self.udp_thread = threading.Thread(target=self._udp_listener, daemon=True)
        self.udp_thread.start()

        # Publicar el ultimo frame recibido a 10 Hz
        self.timer = self.create_timer(0.1, self._publish_frame)

        self.get_logger().info(f"Escuchando frames UDP en puerto {LISTEN_PORT}...")
        self.get_logger().info(f"Publicando en: {PUBLISH_TOPIC}")

    def _udp_listener(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 131072)  # 128KB buffer
        sock.bind(('0.0.0.0', LISTEN_PORT))
        sock.settimeout(2.0)

        frames_received = 0
        while True:
            try:
                # Recibir hasta 65536 bytes (maximo UDP)
                data, addr = sock.recvfrom(65536)

                if len(data) < 4:
                    continue

                # Leer cabecera de 4 bytes con el tamano
                size = struct.unpack('>I', data[:4])[0]
                jpg_bytes = data[4:]

                if len(jpg_bytes) != size:
                    self.get_logger().warn(f"Frame incompleto: {len(jpg_bytes)}/{size} bytes")
                    continue

                # Decodificar JPEG a imagen OpenCV
                np_arr = np.frombuffer(jpg_bytes, dtype=np.uint8)
                frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

                if frame is not None:
                    # Corregir sobreexposicion antes de guardar el frame
                    frame = cv2.convertScaleAbs(frame, alpha=EXPOSURE_ALPHA, beta=EXPOSURE_BETA)
                    with self.lock:
                        self.latest_frame = frame
                    frames_received += 1
                    if frames_received % 30 == 0:
                        h, w = frame.shape[:2]
                        self.get_logger().info(
                            f"Recibidos {frames_received} frames ({w}x{h})"
                        )

            except socket.timeout:
                self.get_logger().warn("Sin frames UDP en los ultimos 2 segundos...")
            except Exception as e:
                self.get_logger().error(f"Error UDP: {e}")

    def _publish_frame(self):
        with self.lock:
            if self.latest_frame is None:
                return
            frame = self.latest_frame.copy()

        try:
            msg = self.bridge.cv2_to_imgmsg(frame, encoding='bgr8')
            msg.header.stamp = self.get_clock().now().to_msg()
            msg.header.frame_id = 'camera_link'
            self.publisher.publish(msg)
        except Exception as e:
            self.get_logger().error(f"Error publicando: {e}")


def main():
    rclpy.init()
    node = UDPCameraReceiverNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
