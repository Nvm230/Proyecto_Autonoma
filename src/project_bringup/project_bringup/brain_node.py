import rclpy
import random
import math
from rclpy.node import Node
from std_msgs.msg import String
from geometry_msgs.msg import Twist
from sensor_msgs.msg import LaserScan
from rclpy.qos import qos_profile_sensor_data

class BrainNode(Node):
    def __init__(self):
        super().__init__('brain_node')

        # Suscripciones
        self.cmd_sub = self.create_subscription(String, '/voice_commands', self.voice_cmd_callback, 10)
        self.det_sub = self.create_subscription(String, '/detected_objects', self.detected_callback, 10)
        
        # EL SECRETO PARA EL ROBOT FÍSICO: El LIDAR físico publica en modo "SensorData" (Best Effort)
        # Si usamos el default (Reliable), ROS 2 ignora los mensajes y el callback nunca se ejecuta.
        self.scan_sub = self.create_subscription(LaserScan, '/scan', self.scan_callback, qos_profile_sensor_data)

        # Publisher de velocidad
        self.cmd_vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)

        # Estado de búsqueda
        self.target_object = None
        self.searching = False
        self.obstacle_ahead = False

        # ---- Parámetros de exploración ----
        self.LINEAR_SPEED  = 0.15   # m/s avanzando
        self.ANGULAR_SPEED = 0.2    # rad/s girando
        self.OBSTACLE_DIST = 0.50   # metros — gira y esquiva si hay algo a menos de 50cm

        # ---- Máquina de estados simple ----
        # Usamos un solo timer de control (10 Hz) y contamos el tiempo internamente.
        # Estados: 'forward' | 'turning'
        self.explore_state = 'idle'
        self.turn_direction = 1.0   # +1 = izquierda, -1 = derecha (se elige aleatoriamente)
        self.state_time = 0.0       # cuánto tiempo llevamos en el estado actual
        self.state_target = 0.0     # cuánto tiempo debe durar el estado actual

        # Timer único de control a 10 Hz
        self.control_timer = self.create_timer(0.1, self.control_loop)
        self.control_timer.cancel()

        self.get_logger().info('Brain Node started. Waiting for voice commands...')

    # ------------------------------------------------------------------ #
    #  LIDAR: detecta obstáculos en el arco frontal (±30°)               #
    # ------------------------------------------------------------------ #
    def scan_callback(self, msg):
        if not self.searching:
            return
        n = len(msg.ranges)
        front_indices = list(range(0, 30)) + list(range(n - 30, n))
        # Filtramos inf, nan y distancias absurdamente pequeñas (ruido/reflejos internos)
        front_ranges = [msg.ranges[i] for i in front_indices
                        if not math.isnan(msg.ranges[i]) and not math.isinf(msg.ranges[i]) and msg.ranges[i] > 0.05]
                        
        valid_all = [r for r in msg.ranges if not math.isnan(r) and not math.isinf(r) and r > 0.05]
        min_all = min(valid_all) if valid_all else -1.0
        
        # LOGS CRUDOS (Se imprimirán siempre que se llame la función para ver qué está pasando)
        self.get_logger().info(f'[DEBUG LIDAR] N={n} | min_all={min_all:.2f} | front_valid_count={len(front_ranges)}')

        if front_ranges:
            min_dist = min(front_ranges)
            self.obstacle_ahead = min_dist < self.OBSTACLE_DIST
            if min_dist < 1.0:
                self.get_logger().info(f'LIDAR min dist frontal: {min_dist:.2f} m')
        else:
            self.obstacle_ahead = False

    # ------------------------------------------------------------------ #
    #  LOOP ÚNICO DE CONTROL                                              #
    # ------------------------------------------------------------------ #
    def control_loop(self):
        if not self.searching:
            return

        self.state_time += 0.1   # acumulamos 100 ms por iteración
        twist = Twist()

        if self.explore_state == 'forward':
            if self.obstacle_ahead:
                # Obstáculo detectado → girar
                self.get_logger().info('Obstacle! Turning...')
                self._begin_turn()
            else:
                # Seguir avanzando infinitamente hasta ver un obstáculo
                twist.linear.x = self.LINEAR_SPEED

        elif self.explore_state == 'turning':
            if self.state_time >= self.state_target:
                # Giro completado → volver a avanzar
                self._begin_forward()
            else:
                twist.angular.z = self.ANGULAR_SPEED * self.turn_direction

        self.cmd_vel_pub.publish(twist)

    # ------------------------------------------------------------------ #
    #  HELPERS: iniciar avance / iniciar giro                             #
    # ------------------------------------------------------------------ #
    def _begin_forward(self):
        self.explore_state = 'forward'
        self.state_time = 0.0
        self.get_logger().info('Moving forward until obstacle detected...')

    def _begin_turn(self):
        self.explore_state = 'turning'
        self.state_time = 0.0
        # Gira entre 45° y 120° en lugar de 90°-180° para no quedarse dando la vuelta en U siempre
        angle = random.uniform(math.pi / 4, 2 * math.pi / 3)   
        self.state_target = angle / self.ANGULAR_SPEED  # duración en segundos
        self.turn_direction = random.choice([-1.0, 1.0])
        side = 'LEFT' if self.turn_direction > 0 else 'RIGHT'
        self.get_logger().info(f'Turning {math.degrees(angle):.0f}° to the {side}')

    # ------------------------------------------------------------------ #
    #  COMANDOS DE VOZ                                                    #
    # ------------------------------------------------------------------ #
    def voice_cmd_callback(self, msg):
        command = msg.data.lower()
        self.get_logger().info(f'Received voice command: {command}')

        if 'buscar botella' in command or 'search bottle' in command:
            self.start_search('bottle')
        elif 'buscar celular' in command or 'search cell phone' in command or 'search phone' in command:
            self.start_search('cell phone')
        elif 'stop' in command or 'alto' in command:
            self.stop_search()

    # ------------------------------------------------------------------ #
    #  INICIO / FIN DE BÚSQUEDA                                           #
    # ------------------------------------------------------------------ #
    def start_search(self, obj_name):
        if self.searching:
            self.stop_search()

        self.target_object = obj_name
        self.searching = True
        self.obstacle_ahead = False

        self.get_logger().info(f'=== SEARCHING FOR: {obj_name.upper()} ===')
        self._begin_forward()
        self.control_timer.reset()

    def stop_search(self):
        self.searching = False
        self.explore_state = 'idle'
        self.target_object = None
        self.control_timer.cancel()
        self.cmd_vel_pub.publish(Twist())   # parar ruedas
        self.get_logger().info('Search stopped. Robot halted.')

    # ------------------------------------------------------------------ #
    #  DETECCIÓN DE OBJETO                                                #
    # ------------------------------------------------------------------ #
    def detected_callback(self, msg):
        if not self.searching or not self.target_object:
            return
        detected = msg.data.split(',')
        if self.target_object in detected:
            self.get_logger().info(f'*** TARGET FOUND: {self.target_object.upper()} *** STOPPING!')
            self.stop_search()


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
