import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    pkg_gazebo_ros = get_package_share_directory('gazebo_ros')
    pkg_tb3_simulations = get_package_share_directory('turtlebot3_gazebo')
    pkg_nav2_bringup = get_package_share_directory('nav2_bringup')
    pkg_project = get_package_share_directory('project_bringup')
    
    world_path = os.path.join(pkg_project, 'worlds', 'custom_house.world')
    urdf_path = os.path.join(pkg_project, 'urdf', 'turtlebot3_waffle_pi_custom.urdf')
    map_path = os.path.join(pkg_project, 'maps', 'empty_map.yaml')
    params_path = os.path.join(pkg_project, 'config', 'nav2_params.yaml')
    
    # Environment variable for TB3 model, needed by TB3 launch files
    os.environ['TURTLEBOT3_MODEL'] = 'waffle_pi'
    
    # We need to add the project models to the GAZEBO_MODEL_PATH
    project_models = os.path.join(pkg_project, 'models')
    user_models = os.path.expanduser('~/.gazebo/models')
    tb3_models = os.path.join(pkg_tb3_simulations, 'models')
    model_paths = f"{project_models}:{user_models}:{tb3_models}"
    
    if 'GAZEBO_MODEL_PATH' in os.environ:
        os.environ['GAZEBO_MODEL_PATH'] += ':' + model_paths
    else:
        os.environ['GAZEBO_MODEL_PATH'] = model_paths

    gzserver_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_gazebo_ros, 'launch', 'gzserver.launch.py')
        ),
        launch_arguments={'world': world_path}.items()
    )

    gzclient_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_gazebo_ros, 'launch', 'gzclient.launch.py')
        )
    )

    robot_state_publisher_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_tb3_simulations, 'launch', 'robot_state_publisher.launch.py')
        ),
        launch_arguments={'use_sim_time': 'true'}.items()
    )
    
    # We spawn our custom urdf
    spawn_turtlebot_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_tb3_simulations, 'launch', 'spawn_turtlebot3.launch.py')
        ),
        launch_arguments={
            'x_pose': '-2.0',
            'y_pose': '1.0'
        }.items()
    )

    # Nav2 Bringup directly
    nav2_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_nav2_bringup, 'launch', 'bringup_launch.py')
        ),
        launch_arguments={
            'use_sim_time': 'true',
            'map': map_path,
            'params_file': params_path
        }.items()
    )

    # RViz2
    rviz_config_dir = os.path.join(get_package_share_directory('turtlebot3_navigation2'), 'rviz', 'tb3_navigation2.rviz')
    rviz_cmd = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        arguments=['-d', rviz_config_dir],
        parameters=[{'use_sim_time': True}],
        output='screen'
    )

    ld = LaunchDescription()
    ld.add_action(gzserver_cmd)
    ld.add_action(gzclient_cmd)
    ld.add_action(robot_state_publisher_cmd)
    ld.add_action(spawn_turtlebot_cmd)
    ld.add_action(nav2_cmd)
    ld.add_action(rviz_cmd)
    
    return ld
