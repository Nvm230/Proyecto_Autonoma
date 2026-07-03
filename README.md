# Módulo de Navegación Autónoma - Rama Caleb

Este módulo contiene el avance y la optimización de la lógica de Navegación Autónoma para el TurtleBot3 Waffle Pi bajo ROS 2 Humble. El sistema está configurado utilizando un planificador local robusto para interiores que previene los fallos por cancelación repentina de ruta (Goal Aborted) al interactuar con mapas dinámicos.

---

## 1. Requisitos e Instalación de Paquetes

Si ejecutan este código de forma nativa en su sistema o quieren asegurar que el entorno cuente con todas las dependencias necesarias, deben instalar los siguientes paquetes fundamentales de ROS 2:

sudo apt update && sudo apt install -y \
  ros-humble-turtlebot3-navigation2 \
  ros-humble-turtlebot3-cartographer \
  ros-humble-nav2-bringup \
  ros-humble-turtlebot3-simulations \
  ros-humble-diagnostic-updater \
  ros-humble-nav2-navfn-planner

---

## 2. Instrucciones de Ejecución en Simulación (Gazebo)

Para arrancar el entorno de pruebas completo, configure las variables de entorno básicas ejecutando las siguientes instrucciones divididas en pestañas independientes de la terminal:

### Terminal 1: Lanzar el Laberinto Virtual (Gazebo)
export LIBGL_ALWAYS_SOFTWARE=1
export TURTLEBOT3_MODEL=waffle_pi
source /opt/ros/humble/setup.bash
ros2 launch turtlebot3_gazebo turtlebot3_house.launch.py
*Nota: Espere a que cargue la interfaz de Gazebo por completo con el robot visible antes de continuar.*

### Terminal 2: Activación de Cartographer (SLAM Dinámico)
export LIBGL_ALWAYS_SOFTWARE=1
export TURTLEBOT3_MODEL=waffle_pi
source /opt/ros/humble/setup.bash
ros2 launch turtlebot3_cartographer cartographer.launch.py use_sim_time:=true

### Terminal 3: Inicialización de Nav2 (Motores de Navegación)
export TURTLEBOT3_MODEL=waffle_pi
source /opt/ros/humble/setup.bash
ros2 launch nav2_bringup navigation_launch.py use_sim_time:=true autostart:=true map_subscribe_transient_local:=true

### Terminal 4: Interfaz Gráfica de Control (RViz2)
export LIBGL_ALWAYS_SOFTWARE=1
export TURTLEBOT3_MODEL=waffle_pi
source /opt/ros/humble/setup.bash
ros2 launch nav2_bringup rviz_launch.py use_sim_time:=true

*¿Cómo moverlo?: En la ventana de RViz2 verán el mapa a color. Hagan clic en el botón 'Nav2 Goal' de la barra superior, seleccionen un punto libre dentro del laberinto, arrastren el cursor para indicar la orientación deseada y suéltenlo. El robot se desplazará de inmediato de forma autónoma.*

---

## 3. Guía para la Tarea: Modificación de la Posición del LiDAR

Para cumplir con el requerimiento de la entrega sobre alterar la posición del sensor de distancia (LiDAR) y actualizar el árbol de transformaciones estáticas (tf), editen el archivo descriptivo del robot:

* Ruta del archivo: /opt/ros/humble/share/turtlebot3_gazebo/models/turtlebot3_waffle_pi/model.sdf
* Bloque objetivo: Localicen la etiqueta <link name="base_scan"> y editen los valores dentro del parámetro <pose>:

- Eje X (Longitudinal): El valor por defecto es -0.064. Increméntenlo a positivo si desean desplazar el LiDAR hacia la parte frontal del robot.
- Eje Z (Vertical): El valor por defecto es 0.121. Modifíquenlo si necesitan simular un cambio en la altura del soporte físico del sensor.

*Importante: Tras guardar cualquier cambio en el archivo de configuración del modelo, recuerden limpiar el entorno y ejecutar "colcon build --symlink-install" desde la raíz de su espacio de trabajo para actualizar las lecturas de distancia.*

---

## 4. Consideraciones para Despliegue en el Robot Real (Laboratorio Físico)

Cuando se realice la transición de la simulación al hardware real del TurtleBot3 en los laboratorios, apliquen obligatoriamente las siguientes pautas de red y sincronización:

1. Conexión y Control Base:
Conéctense a la computadora integrada del robot vía SSH (ssh ubuntu@IP_DEL_ROBOT) e inicialicen los motores y sensores de lectura físicos ejecutando:
ros2 launch turtlebot3_bringup robot.launch.py

2. Sincronización de Red (ROS_DOMAIN_ID):
Tanto en la terminal del robot físico como en su propia laptop de desarrollo conectada a la red local del laboratorio, deben exportar el mismo identificador de dominio. Ejemplo:
export ROS_DOMAIN_ID=30

3. El Parámetro Crucial "use_sim_time":
- En Simulación (Gazebo): Se establece estrictamente en "true" porque ROS necesita sincronizarse con el reloj del simulador virtual.
- En Entorno Real (Laboratorio): Al lanzar Cartographer, Nav2 o RViz2 en su PC remota, cambien ese parámetro obligatoriamente a "false" (use_sim_time:=false). De lo contrario, los nodos se quedarán congelados esperando un reloj de simulación que no existe, ignorando los sensores del hardware real.