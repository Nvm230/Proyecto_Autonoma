#!usr/bin/env python3
import rclpy
from rclpy.node import Node
import speech_recognition as sr
from std_msgs.msg import String

class VoiceInteractionNode(Node):
    def __init__(self):
        super().__init__('voice_interaction_node')
        self.publisher_ = self.create_publisher(String, 'voice_commands', 10)
        self.timer = self.create_timer(1.0, self.listen_command)
        self.declare_parameter('device_index', -1)
        device_index = self.get_parameter('device_index').value
        
        # Buscar el dispositivo "pulse" o "default" automáticamente si no se especifica
        if device_index < 0:
            mics = sr.Microphone.list_microphone_names()
            self.get_logger().info(f"Available audio devices: {mics}")
            for i, name in enumerate(mics):
                if name.lower() == 'pulse':
                    device_index = i
                    self.get_logger().info(f"Auto-selected 'pulse' device at index {i}")
                    break
            if device_index < 0:
                device_index = None

        self.recognizer = sr.Recognizer()
        self.get_logger().info(f"Initializing Voice Interaction Node (Device Index: {device_index})...")
        try:
            self.microphone = sr.Microphone(device_index=device_index)
            
            # ¡EL SECRETO! En lugar de usar 'with', abrimos el stream UNA sola vez
            # y lo mantenemos abierto para siempre. Esto evita el Segmentation Fault.
            self.mic_source = self.microphone.__enter__()
            
            self.get_logger().info("Calibrando ruido de fondo... Please wait 2 seconds.")
            self.recognizer.adjust_for_ambient_noise(self.mic_source, duration=2.0)
            # Volvemos a los defaults dinámicos para que no bloquee voces suaves
            self.recognizer.pause_threshold = 0.8
            self.get_logger().info("Microphone ready. You can speak now!")
            self.has_mic = True
        except OSError as e:
            self.get_logger().warning(f"No microphone found or permission denied! Error: {e}")
            self.get_logger().warning("No microphone found! Waiting for text commands on /voice_commands topic instead.")
            self.has_mic = False

    def listen_command(self):
        if not self.has_mic:
            return
            
        try:
            self.get_logger().debug("Listening for a command...")
            # Usamos el stream que ya está abierto desde el __init__
            audio = self.recognizer.listen(self.mic_source, timeout=2.0, phrase_time_limit=5.0)
            
            command = self.recognizer.recognize_google(audio, language="es-ES")
            self.get_logger().info(f"==> COMMAND RECOGNIZED: {command.upper()} <==")
            msg = String()
            msg.data = command
            self.publisher_.publish(msg)
        except sr.WaitTimeoutError:
            pass # normal timeout when nobody speaks
        except sr.UnknownValueError:
            self.get_logger().warn("Google API received audio but couldn't understand any words. (Mic might be capturing static/silence)")
        except sr.RequestError as e:
            self.get_logger().error(f"Google Speech API error (Check internet connection): {e}")
        except Exception as e:
            self.get_logger().error(f"Microphone or processing error: {e}")

def main(args=None):
    rclpy.init(args=args)
    node = VoiceInteractionNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()