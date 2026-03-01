import subprocess

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():

    use_sim_time = LaunchConfiguration('use_sim_time', default='false')

    path_follower= Node(
        package ='qcar2_autonomy',
        executable ='path_follower',
        name ='path_follower',
        parameters=[{'use_sim_time': use_sim_time}]
    )

    traffic_system_detector = Node(
        package ='qcar2_autonomy',
        executable='traffic_system_detector',
        name = 'traffic_system_detector',
        parameters=[{'use_sim_time': use_sim_time}]
    )
    trip_planner = Node(
        package ='qcar2_autonomy',
        executable='trip_planner',
        name = 'trip_planner',
        parameters=[{'use_sim_time': use_sim_time}]
    )

    ''' TODO: Once finished this launch file must also include
    - Lane detector to help smooth out tracking of lanes while driving
    - Planner server to coordinate which LEDs on the QCar should be on based on trip logic
    '''

    return LaunchDescription([
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='false',
            description='Use simulation (Gazebo) clock if true'),
        path_follower,
        traffic_system_detector,
        trip_planner]
    )