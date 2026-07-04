# Proyecto Autónoma: Robot de Búsqueda con ROS 2 y YOLOv8

Este proyecto implementa un robot TurtleBot3 autónomo en un entorno simulado de Gazebo utilizando ROS 2 (Humble). El robot es capaz de recibir comandos de voz, navegar inteligentemente por un mapa conocido usando Nav2, y utilizar visión artificial (YOLOv8) para buscar y detectar objetos específicos (como botellas y celulares).

## Requisitos Previos

- **Sistema Operativo:** Ubuntu 22.04 LTS (Jammy Jellyfish).
- **ROS 2:** Humble Hawksbill.
- **Python 3:** Con las librerías necesarias (Ultralytics YOLO, SpeechRecognition, PyAudio, OpenCV, etc).

---

## 1. Compilación del Espacio de Trabajo

Abre una terminal y ve a la raíz de tu proyecto (donde se encuentra la carpeta `src`):

```bash
cd ~/Documents/Proyecto_Autonoma
source /opt/ros/humble/setup.bash
colcon build
```

Una vez terminada la compilación, **siempre** debes hacer *source* al archivo de instalación para que ROS 2 reconozca tus paquetes. En la misma terminal ejecuta:

```bash
source install/setup.bash
```

---

## 2. Ejecutar la Simulación y Nav2

Para iniciar el entorno virtual (Gazebo) junto con el mapa de la casa, el robot y el sistema de navegación Nav2 (AMCL), asegúrate de haber compilado y haz source en tu **Terminal 1**:

```bash
source /opt/ros/humble/setup.bash
source install/setup.bash
ros2 launch project_bringup simulation_launch.py
```

*Nota: La primera vez que se abre Gazebo, puede tardar un poco en cargar. Verás el entorno de la casa virtual, y en RViz2 podrás ver el mapa.*

---

## 3. Ejecutar la Lógica de Comportamiento (Cerebro, Visión y Voz)

Una vez que la simulación esté cargada por completo y viendo el mapa en RViz, abre una **Terminal 2**, prepara tu entorno de ROS 2 y ejecuta:

```bash
# Preparar el entorno
cd ~/Documents/Proyecto_Autonoma
source /opt/ros/humble/setup.bash
source install/setup.bash

# Lanzar el cerebro, el detector de objetos y el micrófono
ros2 launch project_bringup behavior_launch.py
```

Este archivo lanzará simultáneamente 3 cosas:
1. **El Nodo de Interacción por Voz:** Que escuchará tu micrófono constantemente.
2. **El Nodo Cerebro:** Que gestionará la navegación, buscará por las habitaciones y controlará al robot.
3. **El Nodo Detector (YOLO):** Que usará la cámara del robot para buscar los objetos deseados usando inteligencia artificial.

---

## 4. Uso del Sistema

Cuando ambos terminales estén ejecutándose, el sistema estará listo.
Habla directamente a tu micrófono. Los comandos que el robot entiende incluyen:

- **"botella"**: El robot iniciará la ruta de exploración hacia las coordenadas predefinidas (habitaciones) intentando detectar una botella verde con su cámara.
- **"celular"** o **"móvil"**: El robot iniciará la búsqueda de un teléfono celular.

Si el robot detecta visualmente el objeto, detendrá la navegación, se girará un poco para "celebrar" (spin) y abortará la búsqueda, dando por cumplida su misión.

---

## Resolución de Problemas

- **Si la simulación se queda con la pantalla en negro (Error 255):** Probablemente Gazebo se haya quedado colgado en segundo plano. Cierra todas las terminales y corre los siguientes comandos de limpieza antes de intentar de nuevo:
  ```bash
  killall -9 gzserver gzclient rviz2 python3
  rm -rf ~/.gazebo/client-* ~/.gazebo/server-* ~/.gazebo/log/*
  ```
- **Si AMCL no encuentra el mapa o tira errores TF:** Asegúrate de estar ejecutando los archivos *launch* en el orden correcto y de haber hecho `colcon build` si modificaste parámetros de configuración en la carpeta `config`.
