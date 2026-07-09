import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.substitutions import LaunchConfiguration
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

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
        
    pkg_nav2_bringup = get_package_share_directory('nav2_bringup')
    pkg_project = get_package_share_directory('project_bringup')
    params_path = os.path.join(pkg_project, 'config', 'nav2_params.yaml')
    map_path = os.path.join(pkg_project, 'maps', 'empty_map.yaml')
    
    # Nav2 Bringup with SLAM enabled
    nav2_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_nav2_bringup, 'launch', 'bringup_launch.py')
        ),
        launch_arguments={
            'use_sim_time': use_sim_time,
            'slam': 'True',
            'map': map_path,
            'params_file': params_path
        }.items()
    )

    # RViz2 for visualization
    rviz_config_path = os.path.join(pkg_nav2_bringup, 'rviz', 'nav2_default_view.rviz')
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        arguments=['-d', rviz_config_path],
        parameters=[{'use_sim_time': use_sim_time}],
        output='screen'
    )

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
    
    # Brain Node (Clásico)
    brain_node = Node(
        package='project_bringup',
        executable='brain_node_clasico',
        name='brain_node_clasico',
        output='screen',
        parameters=[{'use_sim_time': use_sim_time}]
    )

    ld = LaunchDescription()
    ld.add_action(declare_use_sim_time_cmd)
    ld.add_action(declare_device_index_cmd)
    
    ld.add_action(nav2_cmd)
    ld.add_action(rviz_node)
    
    ld.add_action(detector_node)
    ld.add_action(voice_node)
    ld.add_action(brain_node)
    
    return ld
