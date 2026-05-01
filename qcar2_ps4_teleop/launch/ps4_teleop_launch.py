"""
Launch file for QCar2 PS4 Bluetooth Teleop
──────────────────────────────────────────
Starts:
  1. ps4_teleop_node — reads PS4 D-pad via pygame, publishes /ps4_dpad_cmd
  2. fast_teleop     — subscribes to /ps4_dpad_cmd, publishes MotorCommands

Usage:
  ros2 launch qcar2_ps4_teleop ps4_teleop_launch.py
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():

    pkg_share = get_package_share_directory("qcar2_ps4_teleop")
    params_file = os.path.join(pkg_share, "config", "ps4_params.yaml")

    # ── ps4_teleop_node: reads D-pad, publishes /ps4_dpad_cmd ────────
    ps4_node = Node(
        package="qcar2_ps4_teleop",
        executable="ps4_teleop_node",
        name="ps4_teleop_node",
        parameters=[params_file],
        output="screen",
    )

    return LaunchDescription([
        ps4_node,
    ])
