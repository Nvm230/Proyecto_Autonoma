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
        self.recognizer = sr.Recognizer()
        self.get_logger().info("Initializing Voice Interaction Node...")
        try:
            self.microphone = sr.Microphone()
            self.get_logger().info("Microphone found. Listening...")
            self.has_mic = True
        except OSError:
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
            self.get_logger().info(f"Recognized command: {command}")
            msg = String()
            msg.data = command
            self.publisher_.publish(msg)
        except sr.WaitTimeoutError:
            pass # normal timeout
        except sr.UnknownValueError:
            self.get_logger().warn("Could not understand the audio.")
        except sr.RequestError as e:
            self.get_logger().error(f"Speech Recognition service error: {e}")
        except Exception as e:
            self.get_logger().error(f"Microphone error: {e}")

def main(args=None):
    rclpy.init(args=args)
    node = VoiceInteractionNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()