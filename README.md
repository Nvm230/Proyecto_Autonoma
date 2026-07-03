# Módulo de Navegación Autónoma - Rama Caleb

Este módulo contiene el avance de la parte de Navegación, configurado para recibir cualquier comando de posición o meta (Nav2 Goal) e ir hacia ese punto del mapa de forma fluida en interiores.

## Instrucciones de Ejecución (Solo Navegación)

1. Con el contenedor activo, lanzar la simulación del laberinto:
ros2 launch turtlebot3_gazebo turtlebot3_house.launch.py

2. En otra pestaña, activar Cartographer para el mapa vivo:
ros2 launch turtlebot3_cartographer cartographer.launch.py use_sim_time:=true

3. Lanzar el motor de Nav2 optimizado para que el robot avance al punto sin abortar:
ros2 launch nav2_bringup navigation_launch.py use_sim_time:=true autostart:=true map_subscribe_transient_local:=true

4. Abrir la interfaz de control de RViz2:
ros2 launch nav2_bringup rviz_launch.py use_sim_time:=true

Use el botón 'Nav2 Goal' en la barra superior de RViz2, marque un punto en el mapa y el robot navegará automáticamente hacia allá.
