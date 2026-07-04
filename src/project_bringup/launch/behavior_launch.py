import os
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    # Object Detector Node
    detector_node = Node(
        package='object_detection_ros',
        executable='detector_node',
        name='detector_node',
        output='screen',
        parameters=[{'use_sim_time': True}]
    )
    
    # Voice Interaction Node
    voice_node = Node(
        package='nodes',
        executable='VoiceInteractionNode',
        name='voice_interaction_node',
        output='screen',
        parameters=[{'use_sim_time': True}]
    )
    
    # Brain Node (Behavior and Navigation logic)
    brain_node = Node(
        package='project_bringup',
        executable='brain_node',
        name='brain_node',
        output='screen',
        parameters=[{'use_sim_time': True}]
    )

    ld = LaunchDescription()
    ld.add_action(detector_node)
    ld.add_action(voice_node)
    ld.add_action(brain_node)
    
    return ld
