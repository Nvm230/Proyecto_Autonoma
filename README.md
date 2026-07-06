# Lista de pasos para Actividad 1 - LK

## 1. Conectar al TurtleBot3

### Conectarse a la red WiFi del laboratorio

- **SSID:** `TRENDnet827_2.4GHz_ZE98`
- **Contraseña:** `82772000186`

---

### Configurar las variables de entorno

Editar el archivo con:
```bash
nano ~/.bashrc
```

Añadir al final:
```bash
export ROS_DOMAIN_ID=<ID_DEL_ROBOT>
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
export ROS_LOCALHOST_ONLY=0
```

> Reemplazar `<ID_DEL_ROBOT>` por el número de tres cifras indicado en la etiqueta del robot.

Aplicar los cambios:

```bash
source ~/.bashrc
```

---

### Conectarse al robot por SSH

```bash
ssh ubuntu@192.168.10.<IP_DEL_ROBOT>
```

- Usuario: `ubuntu`
- Contraseña: `turtlebot`

---

### Iniciar el robot (desde la Raspberry Pi)

```bash
ros2 launch turtlebot3_bringup robot.launch.py
```

---

# 2. Crear un mapa (SLAM)

### Iniciar Gazebo

```bash
ros2 launch turtlebot3_gazebo turtlebot3_dqn_stage2.launch.py
```

### Iniciar Cartographer

```bash
ros2 launch turtlebot3_cartographer cartographer.launch.py
```

### Teleoperar el robot

```bash
ros2 run turtlebot3_teleop teleop_keyboard
```

Recorrer completamente el entorno para generar el mapa.

### Guardar el mapa

```bash
ros2 run nav2_map_server map_saver_cli -f ~/map
```

Se generarán los archivos:

```
map.yaml
map.pgm
```

---

# 3. Navegación con un mapa existente

### Iniciar Gazebo

```bash
ros2 launch turtlebot3_gazebo turtlebot3_world.launch.py
```

### Iniciar Nav2

```bash
ros2 launch turtlebot3_navigation2 navigation2.launch.py \
map:=/home/luisk/map.yaml \
use_sim_time:=True
```

> Cambiar la ruta del mapa si se encuentra en otra ubicación.

---

### En RViz

1. Seleccionar **2D Pose Estimate** para indicar la posición inicial del robot.
2. Esperar a que el robot se localice correctamente en el mapa.
3. Seleccionar **Nav2 Goal** y hacer clic sobre el punto destino.

El robot calculará la trayectoria y navegará automáticamente hacia el objetivo.
