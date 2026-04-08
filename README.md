<div align="center">

# :racing_car: Team Seeker — QCar2 Autonomous Driving System

### ACC Self-Driving Competition 2026 — physical Phase

[![ROS 2 Humble](https://img.shields.io/badge/ROS%202-Humble%20Hawksbill-blue?logo=ros&logoColor=white)](https://docs.ros.org/en/humble/)
[![Isaac ROS](https://img.shields.io/badge/NVIDIA-Isaac%20ROS%202.1-76B900?logo=nvidia&logoColor=white)](https://developer.nvidia.com/isaac-ros)
[![TensorRT](https://img.shields.io/badge/TensorRT-Inference-76B900?logo=nvidia&logoColor=white)](https://developer.nvidia.com/tensorrt)
[![Python](https://img.shields.io/badge/Python-3.10-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![C++](https://img.shields.io/badge/C++-17-00599C?logo=cplusplus&logoColor=white)](https://isocpp.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

</div>

---
**INIT QCAR2**
###UPDATING/UPGRADING WITH APT IS PROHIBITED, ESPECIALLY UPGRADING.


The QCar2 OS has Ubuntu 20.0 native and ROS2 Humble installed for interaction with the hardware car but for development we use the Isaac ROS Docker container. In this way, we can have a consistent development environment.

Note: In this case the csi camera number 2 are the front camera.

The system must be started in the following order:
0. Connect to the qcar2.
1. Run the master hardware node (qcar2_nodex) in the NATIVE OS. (Folder = ~/ros2)
2. Run the ROS2 in the Isaac ROS Docker container. (Folder = ~/Documents/ACC_Development/Development/ros2)

# 0. Connect to the qcar2.
Connect to the 5Ghz wifi: SSID: ROSNET15G, PASSWORD: ROSNET2024
In your computer terminal:
```bash
ssh nvidia@qcar-63264.local
```
PASSWORD for all: nvidia

# 1. Native OS without Docker in QCAR2 (Jetson Orin).
```bash
cd ros2
source install/setup.bash
ros2 launch qcar2_nodex qcar2_launch.py
```



# 2. Isaac ROS Docker container in QCAR2 (Jetson Orin).
Initializes the container.
Open a new terminal.
```bash
docker start isaac_ros_dev-aarch64-container
docker attach isaac_ros_dev-aarch64-container
```
Open the DEVELOP Folder.
```bash
cd /workspaces/isaac_ros-dev/ros2
source install/setup.bash
```

IF YOU WANT TO OPEN OTHER TERMINAL, YOU MUST BE FOLLOW THESE STEPS BELOW:
```bash
cd /home/$USER/Documents/ACC_Development/isaac_ros_common
./scripts/run_dev.sh  /home/$USER/Documents/ACC_Development/Development
```
```bash
cd /workspaces/isaac_ros-dev/ros2
source install/setup.bash
```
NOTE: This comand must be executed AFTER initializing the container.

This its all!!


EXTRA OPTIONAL......
Remember compiling steps:
```bash
cd /workspaces/isaac_ros-dev/ros2
cp /workspaces/isaac_ros-dev/ros2/src/utils/yolov8s.onnx /tmp/yolov8s.onnx
```
```bash
cd /workspaces/isaac_ros-dev/ros2
colcon build --packages-up-to qcar2_behavior_tree qcar2_teleop qcar2_planner lane_mapping_acc qcar2_mixer --parallel-workers 3
```

---
