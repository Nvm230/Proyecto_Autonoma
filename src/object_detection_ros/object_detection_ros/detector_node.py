import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
from ultralytics import YOLO

class DetectorNode(Node):
    def __init__(self):
        super().__init__('detector_node')
        
        # We need to subscribe to the turtlebot camera topic. 
        # Update '/camera/image_raw' if the turtlebot uses a different topic
        self.subscription = self.create_subscription(
            Image,
            '/camera/image_raw',
            self.image_callback,
            10
        )
        
        # Publisher for the annotated image with bounding boxes
        self.publisher = self.create_publisher(Image, '/camera/image_annotated', 10)
        
        self.bridge = CvBridge()
        
        # Use the pre-trained YOLOv8 nano model (COCO dataset)
        self.get_logger().info("Loading pre-trained YOLOv8 model...")
        self.model = YOLO('yolov8n.pt')
        
        # Define the 2 objects you want to detect (must be from the 80 COCO classes)
        # Examples: 'person', 'bottle', 'cell phone', 'cup', 'chair', 'book'
        self.target_classes = ['bottle', 'cell phone']
        
        # Get the class IDs for the target classes
        self.target_class_ids = []
        for class_id, class_name in self.model.names.items():
            if class_name in self.target_classes:
                self.target_class_ids.append(class_id)
                
        self.get_logger().info(f"Detector Node has been started. Filtering for: {self.target_classes}")

    def image_callback(self, msg):
        try:
            # Convert ROS Image message to OpenCV image
            cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
            
            # Run YOLOv8 inference, filtering for only our target classes
            results = self.model(cv_image, classes=self.target_class_ids, verbose=False)
            
            # Get annotated image
            annotated_frame = results[0].plot()
            
            # Convert back to ROS Image message and publish
            annotated_msg = self.bridge.cv2_to_imgmsg(annotated_frame, encoding="bgr8")
            self.publisher.publish(annotated_msg)
            
        except Exception as e:
            self.get_logger().error(f"Error processing image: {e}")

def main(args=None):
    rclpy.init(args=args)
    node = DetectorNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
