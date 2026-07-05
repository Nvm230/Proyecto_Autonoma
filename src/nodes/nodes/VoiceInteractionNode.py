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
        if device_index < 0:
            device_index = None

        self.recognizer = sr.Recognizer()
        self.get_logger().info(f"Initializing Voice Interaction Node (Device Index: {device_index})...")
        try:
            self.microphone = sr.Microphone(device_index=device_index)
            with self.microphone as source:
                self.get_logger().info("Calibrating microphone for ambient noise... Please wait 2 seconds.")
                self.recognizer.adjust_for_ambient_noise(source, duration=2.0)
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
            with self.microphone as source:
                self.get_logger().debug("Listening for a command...")
                audio = self.recognizer.listen(source, timeout=2.0, phrase_time_limit=5.0)
            
            command = self.recognizer.recognize_google(audio, language="es-ES")
            self.get_logger().info(f"==> COMMAND RECOGNIZED: {command.upper()} <==")
            msg = String()
            msg.data = command
            self.publisher_.publish(msg)
        except sr.WaitTimeoutError:
            pass # normal timeout when nobody speaks
        except sr.UnknownValueError:
            self.get_logger().debug("Heard non-speech noise, ignoring.")
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