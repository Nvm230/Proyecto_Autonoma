#!usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from geometry_msgs.msg import Twist

class CommandInterpreter(Node):
    def __init__(self):
        super().__init__('command_interpreter')
        self.subscription = self.create_subscription(
            String,
            'voice_commands',
            self.listener_callback,
            10)
        self.publisher_ = self.create_publisher(Twist, 'cmd_vel', 10)
        self.get_logger().info("Command Interpreter Node started.")

    def listener_callback(self, msg):
        command = msg.data.lower()
        twist = Twist()

        if "forward" in command:
            twist.linear.x = 0.2
        elif "backward" in command:
            twist.linear.x = -0.2
        elif "left" in command:
            twist.angular.z = 0.5
        elif "right" in command:
            twist.angular.z = -0.5
        elif "stop" in command:
            twist.linear.x = 0.0
            twist.angular.z = 0.0

        self.publisher_.publish(twist)
        self.get_logger().info(f"Executing command: {command}")

def main(args=None):
    rclpy.init(args=args)
    node = CommandInterpreter()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()