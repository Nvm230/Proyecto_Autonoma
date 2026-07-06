import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
import cv2

class CameraNode(Node):
    def __init__(self):
        super().__init__('raw_camera_node')
        self.pub = self.create_publisher(Image, '/camera/image_raw', 1)
        # 0 usually maps to the first USB camera (/dev/video0)
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        if not self.cap.isOpened():
            self.get_logger().error("Error: ¡Linux no me deja abrir la cámara USB!")
            
        self.timer = self.create_timer(0.1, self.timer_callback)
        self.get_logger().info("🔥 ¡Cámara encendida a la fuerza vía Python! Publicando video...")
        
    def timer_callback(self):
        ret, frame = self.cap.read()
        if ret:
            # Mostrar la imagen nativamente en la laptop para confirmar que funciona
            cv2.imshow("TEST NATIVO (Ignora esta ventana)", frame)
            cv2.waitKey(1)
            
            msg = Image()
            msg.header.stamp = self.get_clock().now().to_msg()
            msg.header.frame_id = 'camera_link'
            msg.height = frame.shape[0]
            msg.width = frame.shape[1]
            msg.encoding = 'bgr8'
            msg.is_bigendian = 0
            msg.step = frame.shape[1] * 3
            msg.data = frame.tobytes()
            self.pub.publish(msg)

def main():
    rclpy.init()
    node = CameraNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.cap.release()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
