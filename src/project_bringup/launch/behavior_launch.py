import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    use_sim_time = LaunchConfiguration('use_sim_time')
    device_index = LaunchConfiguration('device_index')
    
    declare_use_sim_time_cmd = DeclareLaunchArgument(
        'use_sim_time',
        default_value='false',
        description='Use simulation (Gazebo) clock if true')

    declare_device_index_cmd = DeclareLaunchArgument(
        'device_index',
        default_value='-1',
        description='PyAudio device index for microphone (-1 for default)')
    # Object Detector Node
    detector_node = Node(
        package='object_detection_ros',
        executable='detector_node',
        name='detector_node',
        output='screen',
        parameters=[{'use_sim_time': use_sim_time}]
    )
    
    # Voice Interaction Node
    voice_node = Node(
        package='nodes',
        executable='VoiceInteractionNode',
        name='voice_interaction_node',
        output='screen',
        parameters=[{
            'use_sim_time': use_sim_time,
            'device_index': device_index
        }]
    )
    
    # Brain Node (Behavior and Navigation logic)
    brain_node = Node(
        package='project_bringup',
        executable='brain_node',
        name='brain_node',
        output='screen',
        parameters=[{'use_sim_time': use_sim_time}]
    )

    ld = LaunchDescription()
    ld.add_action(declare_use_sim_time_cmd)
    ld.add_action(declare_device_index_cmd)
    ld.add_action(detector_node)
    ld.add_action(voice_node)
    ld.add_action(brain_node)
    
    return ld
