#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from rclpy.action import ActionClient
from nav2_msgs.action import NavigateToPose
from geometry_msgs.msg import PoseStamped
import subprocess
import threading
import time

class BrainNode(Node):
    def __init__(self):
        super().__init__('brain_node')
        
        self.explore_process = None
        self.nav2_ready = False
        
        # Suscriptor a comandos de voz
        self.create_subscription(String, '/voice_commands', self.voice_cmd_callback, 10)
        
        # Cliente de acción para Nav2
        self.nav_client = ActionClient(self, NavigateToPose, 'navigate_to_pose')
        
        self.get_logger().info('⏳ Esperando a que el "Cerebro" de Nav2 y SLAM se inicien (esto puede tomar unos 10 segundos)...')
        
        # Hilo en segundo plano para esperar a Nav2 sin bloquear el nodo
        self.wait_thread = threading.Thread(target=self.wait_for_nav2)
        self.wait_thread.start()

    def wait_for_nav2(self):
        # Esperamos a que el servidor de acciones de Nav2 esté disponible
        self.nav_client.wait_for_server()
        
        # Damos unos segundos extra de gracia para asegurarnos de que todos los nodos lifecycle 
        # (bt_navigator, controller_server, etc.) pasen de "Configuring" a "Active"
        time.sleep(5.0)
        
        self.nav2_ready = True
        self.get_logger().info('=========================================')
        self.get_logger().info('✅ SETUP LISTO - SISTEMA 100% OPERATIVO ✅')
        self.get_logger().info('=========================================')
        self.get_logger().info('👉 Ahora puedes decir "Buscar [objeto]" o "Ir a la puerta"')

    def voice_cmd_callback(self, msg):
        cmd = msg.data.lower()
        self.get_logger().info(f'Received voice command: "{cmd}"')
        
        if not self.nav2_ready:
            self.get_logger().warn('⚠️ Nav2 todavía se está iniciando. Por favor, espera el mensaje de SETUP LISTO.')
            return

        if cmd.startswith("buscar"):
            objeto = cmd.replace("buscar ", "")
            self.get_logger().info(f'--- INICIANDO BÚSQUEDA INTELIGENTE: {objeto} ---')
            self.iniciar_exploracion()
            
        elif "puerta" in cmd:
            self.get_logger().info('--- REGRESANDO A LA PUERTA (0, 0) ---')
            self.detener_exploracion()
            self.volver_a_origen()
            
        elif "detente" in cmd or "alto" in cmd:
            self.get_logger().info('--- DETENIENDO ROBOT ---')
            self.detener_exploracion()
            # Cancelar cualquier navegación activa
            self.nav_client._cancel_goal_async()
            self.get_logger().info('Motores frenados.')

    def iniciar_exploracion(self):
        self.detener_exploracion()
        
        self.get_logger().info('Lanzando Explore Lite (algoritmo de fronteras)...')
        self.explore_process = subprocess.Popen([
            'ros2', 'launch', 'explore_lite', 'explore.launch.py'
        ])

    def detener_exploracion(self):
        if self.explore_process is not None:
            self.get_logger().info('Deteniendo algoritmo de exploración...')
            self.explore_process.terminate()
            self.explore_process.wait()
            self.explore_process = None

    def volver_a_origen(self):
        goal_msg = NavigateToPose.Goal()
        goal_msg.pose.header.frame_id = 'map'
        goal_msg.pose.header.stamp = self.get_clock().now().to_msg()
        
        # Origen (x=0, y=0)
        goal_msg.pose.pose.position.x = 0.0
        goal_msg.pose.pose.position.y = 0.0
        goal_msg.pose.pose.position.z = 0.0
        
        # Orientación neutra (sin rotación)
        goal_msg.pose.pose.orientation.x = 0.0
        goal_msg.pose.pose.orientation.y = 0.0
        goal_msg.pose.pose.orientation.z = 0.0
        goal_msg.pose.pose.orientation.w = 1.0
        
        self.get_logger().info('Enviando coordenada (0, 0) a Nav2...')
        self.nav_client.send_goal_async(goal_msg)

def main(args=None):
    rclpy.init(args=args)
    node = BrainNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.detener_exploracion()
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
