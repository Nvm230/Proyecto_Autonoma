#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import LaserScan
from geometry_msgs.msg import Twist
import math

class ReactiveExplorerNode(Node):
    def __init__(self):
        super().__init__('reactive_explorer')
        
        # Parámetros de velocidad y distancia
        self.forward_speed = 0.15
        self.turn_speed = 0.4
        self.safe_distance = 0.5  # Metros
        self.view_angle = 60  # Grados hacia cada lado desde el frente (0)
        
        # Estado
        self.is_turning = False
        
        # Publisher y Subscriber
        self.cmd_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.scan_sub = self.create_subscription(LaserScan, '/scan', self.scan_callback, qos_profile_sensor_data)
        
        # Timer de control
        self.timer = self.create_timer(0.1, self.control_loop)
        
        self.get_logger().info('🚀 Explorador Reactivo Iniciado. Avanzando y esquivando obstáculos...')

    def scan_callback(self, msg):
        # El frente es el índice 0. Los índices aumentan en sentido antihorario.
        # Rango a revisar: [0 a view_angle] y [360-view_angle a 359]
        
        ranges = msg.ranges
        num_ranges = len(ranges)
        
        if num_ranges == 0:
            return
            
        # Calcular los índices equivalentes a los grados
        # (Asumiendo que num_ranges es típicamente 360)
        angle_increment = math.degrees(msg.angle_increment)
        if angle_increment <= 0.0:
            angle_increment = 360.0 / num_ranges
            
        indices_to_check = int(self.view_angle / angle_increment)
        
        front_ranges = []
        
        # Recolectar datos del frente izquierdo (0 a view_angle)
        for i in range(0, min(indices_to_check, num_ranges)):
            r = ranges[i]
            if 0.01 < r < 10.0: # Ignorar solo ruido nulo (0.0)
                front_ranges.append(r)
                
        # Recolectar datos del frente derecho (num_ranges - view_angle a num_ranges - 1)
        for i in range(max(0, num_ranges - indices_to_check), num_ranges):
            r = ranges[i]
            if 0.01 < r < 10.0:
                front_ranges.append(r)
                
        if len(front_ranges) > 0:
            min_dist = min(front_ranges)
            if min_dist < self.safe_distance:
                self.is_turning = True
            else:
                self.is_turning = False
        else:
            # Si no hay datos (todo está muy lejos), el camino está libre
            self.is_turning = False

    def control_loop(self):
        twist = Twist()
        if self.is_turning:
            twist.linear.x = 0.0
            twist.angular.z = self.turn_speed
        else:
            twist.linear.x = self.forward_speed
            twist.angular.z = 0.0
            
        self.cmd_pub.publish(twist)

def main(args=None):
    rclpy.init(args=args)
    node = ReactiveExplorerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        # Detener motores antes de morir si el contexto sigue vivo
        try:
            if rclpy.ok():
                stop_msg = Twist()
                node.cmd_pub.publish(stop_msg)
        except Exception:
            pass
        node.destroy_node()
        try:
            if rclpy.ok():
                rclpy.shutdown()
        except Exception:
            pass

if __name__ == '__main__':
    main()
