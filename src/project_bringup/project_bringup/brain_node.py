import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from std_msgs.msg import String
from geometry_msgs.msg import Twist, PoseStamped, PoseWithCovarianceStamped
from nav2_msgs.action import NavigateToPose
import time
import threading

class BrainNode(Node):
    def __init__(self):
        super().__init__('brain_node')
        
        self.cmd_sub = self.create_subscription(String, '/voice_commands', self.voice_cmd_callback, 10)
        self.det_sub = self.create_subscription(String, '/detected_objects', self.detected_callback, 10)
        
        self.cmd_vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.initial_pose_pub = self.create_publisher(PoseWithCovarianceStamped, '/initialpose', 10)
        self.nav_client = ActionClient(self, NavigateToPose, 'navigate_to_pose')
        
        self.target_object = None
        self.searching = False
        self.nav_goal_handle = None
        
        self.spin_timer = self.create_timer(0.2, self.spin_timer_callback)
        self.spin_timer.cancel()
        self.fallback_spinning = False
        
        self.search_waypoints = [
            (0.5, 0.5),   # Center room
            (3.5, 1.0),   # Right room (bottle)
            (2.0, 3.0),   # Top room (cellphone)
            (-2.0, 1.0)   # Spawn room
        ]
        self.current_waypoint_idx = 0
        
        self.waypoint_spin_timer = self.create_timer(15.0, self.done_spinning_callback)
        self.waypoint_spin_timer.cancel()
        
        self.get_logger().info('Brain Node started. Waiting for voice commands...')

    def voice_cmd_callback(self, msg):
        command = msg.data.lower()
        self.get_logger().info(f'Received voice command: {command}')
        
        if 'door' in command or 'puerta' in command:
            self.get_logger().info('Test 1: Navigating to the door...')
            self.navigate_to_door()
            
        elif 'bottle' in command or 'botella' in command:
            self.get_logger().info('Test 2: Searching for bottle...')
            self.start_search('bottle')
            
        elif 'cell' in command or 'celular' in command or 'phone' in command:
            self.get_logger().info('Test 2: Searching for cell phone...')
            self.start_search('cell phone')
            
        elif 'stop' in command or 'alto' in command:
            self.stop_robot()
            self.searching = False
            self.fallback_spinning = False
            self.spin_timer.cancel()
            self.waypoint_spin_timer.cancel()

    def navigate_to_door(self):
        # Coordinates for the door in turtlebot3_house
        door_pose = PoseStamped()
        door_pose.header.frame_id = 'map'
        door_pose.header.stamp = self.get_clock().now().to_msg()
        door_pose.pose.position.x = 2.0
        door_pose.pose.position.y = -2.5
        door_pose.pose.orientation.w = 1.0
        self.send_nav_goal(door_pose)

    def start_search(self, obj_name):
        self.target_object = obj_name
        self.searching = True
        self.current_waypoint_idx = 0
        
        self.get_logger().info('Starting exploration search...')
        self.navigate_to_next_waypoint()
        
    def navigate_to_next_waypoint(self):
        if self.current_waypoint_idx >= len(self.search_waypoints):
            self.get_logger().info('Finished searching all waypoints. Object not found.')
            self.searching = False
            self.stop_robot()
            return
            
        wx, wy = self.search_waypoints[self.current_waypoint_idx]
        self.get_logger().info(f'Navigating to waypoint {self.current_waypoint_idx + 1}: ({wx}, {wy})')
        
        search_pose = PoseStamped()
        search_pose.header.frame_id = 'map'
        search_pose.header.stamp = self.get_clock().now().to_msg()
        search_pose.pose.position.x = wx
        search_pose.pose.position.y = wy
        search_pose.pose.orientation.w = 1.0
        
        self.send_nav_goal(search_pose)
        
        # We will also start spinning when we reach there, or just spin if already there.
        # For simplicity, if we are already searching, the detection callback will stop us.

    def detected_callback(self, msg):
        if not self.searching or not self.target_object:
            return
            
        detected = msg.data.split(',')
        # Map target to possible YOLOv8 detections (simulation objects might look different to AI)
        acceptable_detections = [self.target_object]
        if self.target_object == 'bottle':
            acceptable_detections.extend(['cup', 'vase', 'wine glass'])
            
        if any(item in detected for item in acceptable_detections):
            self.get_logger().info(f'*** TARGET FOUND: {self.target_object.upper()} ***')
            self.searching = False
            self.fallback_spinning = False
            self.spin_timer.cancel()
            self.waypoint_spin_timer.cancel()
            self.target_object = None
            self.stop_robot()

    def stop_robot(self):
        if self.nav_goal_handle:
            self.get_logger().info('Canceling navigation goal...')
            self.nav_goal_handle.cancel_goal_async()
            
        twist = Twist()
        self.cmd_vel_pub.publish(twist)

    def send_nav_goal(self, pose):
        if not self.nav_client.wait_for_server(timeout_sec=2.0):
            self.get_logger().error('NavigateToPose action server not available! Falling back to spinning in place for search.')
            if self.searching:
                self.fallback_spinning = True
                self.spin_timer.reset()
            return
            
        goal_msg = NavigateToPose.Goal()
        goal_msg.pose = pose
        
        self.get_logger().info('Sending navigation goal...')
        send_goal_future = self.nav_client.send_goal_async(goal_msg)
        send_goal_future.add_done_callback(self.goal_response_callback)

    def goal_response_callback(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().error('Navigation goal rejected')
            return
            
        self.get_logger().info('Navigation goal accepted')
        self.nav_goal_handle = goal_handle
        
        get_result_future = goal_handle.get_result_async()
        get_result_future.add_done_callback(self.get_result_callback)

    def get_result_callback(self, future):
        status = future.result().status
        self.nav_goal_handle = None
        if status == 4: # SUCCEEDED
            self.get_logger().info('Goal succeeded!')
            if self.searching:
                # If we reached the waypoint and haven't found it, spin around for 15 seconds
                self.get_logger().info('Spinning to look around this waypoint...')
                self.fallback_spinning = True
                self.spin_timer.reset()
                self.waypoint_spin_timer.reset()
        else:
            self.get_logger().info(f'Goal failed with status: {status}')

    def spin_timer_callback(self):
        if self.fallback_spinning:
            twist = Twist()
            twist.angular.z = 0.5
            self.cmd_vel_pub.publish(twist)
            
    def done_spinning_callback(self):
        if self.searching and self.fallback_spinning:
            self.get_logger().info('Finished spinning at current waypoint. Moving to next.')
            self.fallback_spinning = False
            self.spin_timer.cancel()
            self.waypoint_spin_timer.cancel()
            
            self.current_waypoint_idx += 1
            self.navigate_to_next_waypoint()

def main(args=None):
    rclpy.init(args=args)
    node = BrainNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
