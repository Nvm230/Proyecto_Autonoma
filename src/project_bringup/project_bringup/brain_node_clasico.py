#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from rclpy.action import ActionClient
from nav2_msgs.action import NavigateToPose
from geometry_msgs.msg import PoseStamped, Twist
import subprocess
import threading
import time
import os
import signal

class BrainNodeClasico(Node):
    def __init__(self):
        super().__init__('brain_node_clasico')
        
        if not self.has_parameter('use_sim_time'):
            self.declare_parameter('use_sim_time', False)
        
        self.explore_process = None
        self.nav2_ready = False
        self.target_object = None
        
        # Suscriptor a comandos de voz
        self.create_subscription(String, '/voice_commands', self.voice_cmd_callback, 10)
        
        # Publicador para frenar los motores
        self.cmd_vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        
        # Suscriptor a objetos detectados por YOLO
        self.create_subscription(String, '/detected_objects', self.object_detected_callback, 10)
        
        # Cliente de acción para Nav2
        self.nav_client = ActionClient(self, NavigateToPose, 'navigate_to_pose')
        
        self.get_logger().info('⏳ Esperando a que el "Cerebro" de Nav2 y SLAM se inicien (esto puede tomar unos 10 segundos)...')
        
        # Hilo en segundo plano para esperar a Nav2 sin bloquear el nodo
        self.wait_thread = threading.Thread(target=self.wait_for_nav2)
        self.wait_thread.start()

    def wait_for_nav2(self):
        self.get_logger().info('Esperando a Nav2...')
        self.nav_client.wait_for_server()
        time.sleep(5.0)
        self.nav2_ready = True
        self.get_logger().info('=========================================')
        self.get_logger().info('✅ SETUP CLÁSICO LISTO - SISTEMA OPERATIVO ✅')
        self.get_logger().info('=========================================')
        self.get_logger().info('👉 Comandos disponibles: "buscar [objeto]", "volver", "alto"')

    def voice_cmd_callback(self, msg):
        cmd = msg.data.lower()
        self.get_logger().info(f'Received voice command: "{cmd}"')
        
        if not self.nav2_ready:
            self.get_logger().warn('⚠️ Nav2 todavía se está iniciando. Por favor, espera el mensaje de SETUP LISTO.')
            return

        if cmd.startswith("buscar"):
            objeto = cmd.replace("buscar ", "").strip()
            self.target_object = objeto
            self.get_logger().info(f'--- BÚSQUEDA CLÁSICA (LIDAR PURO): {objeto} ---')
            self.iniciar_exploracion_clasica()
            
        elif "volver" in cmd:
            self.get_logger().info('--- REGRESANDO AL ORIGEN (0, 0) ---')
            self.detener_exploracion()
            self.volver_a_origen()
            
        elif "detente" in cmd or "alto" in cmd:
            self.get_logger().info('--- DETENIENDO ROBOT ---')
            self.detener_exploracion()
            self.get_logger().info('Motores frenados.')

    def object_detected_callback(self, msg):
        if self.explore_process is None or not self.target_object:
            return  # Ignorar detecciones si no estamos buscando activamente
            
        objeto_detectado = msg.data.lower()
        
        # Lógica de coincidencia Inteligente (Español -> YOLO)
        match_found = False
        if "botella" in self.target_object:
            # Aceptamos tazas y floreros como "botellas" por el bug de Gazebo
            if "bottle" in objeto_detectado or "cup" in objeto_detectado or "vase" in objeto_detectado or "wine glass" in objeto_detectado:
                match_found = True
        elif "celular" in self.target_object or "telefono" in self.target_object:
            if "cell phone" in objeto_detectado:
                match_found = True
        else:
            # Búsqueda genérica directa
            if self.target_object in objeto_detectado:
                match_found = True
                
        if match_found:
            self.get_logger().info(f'¡OBJETO OBJETIVO ENCONTRADO POR YOLO ({objeto_detectado})! Deteniendo exploración clásica...')
            self.target_object = None
            self.detener_exploracion()

    def iniciar_exploracion_clasica(self):
        self.detener_exploracion()
        self.get_logger().info('Lanzando Explorador Reactivo (Lidar directo)...')
        use_sim_time = str(self.get_parameter('use_sim_time').value).lower()
        self.explore_process = subprocess.Popen([
            'ros2', 'run', 'project_bringup', 'reactive_explorer', '--ros-args', '-p', f'use_sim_time:={use_sim_time}'
        ], preexec_fn=os.setsid)

    def detener_exploracion(self):
        # 1. Enviar comando físico de freno a las ruedas
        stop_msg = Twist()
        self.cmd_vel_pub.publish(stop_msg)
        
        # 2. Matar el proceso del explorador si está corriendo
        if self.explore_process is not None:
            self.get_logger().info('Deteniendo algoritmo de exploración y aplicando frenos...')
            try:
                os.killpg(os.getpgid(self.explore_process.pid), signal.SIGINT)
            except ProcessLookupError:
                pass
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
    node = BrainNodeClasico()
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
