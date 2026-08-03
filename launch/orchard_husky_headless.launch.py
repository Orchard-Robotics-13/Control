"""
Launches the orchard world and spawns a Clearpath Husky A300 into it, same
as orchard_husky.launch.py, but with Gazebo's GUI able to run headless
(server only) and RViz2 defaulted on -- meant for perception/navigation
testing rather than world/scene authoring.

Usage:
  ros2 launch orchard_world orchard_husky_headless.launch.py
  ros2 launch orchard_world orchard_husky_headless.launch.py headless:=false   # GUI back on
  ros2 launch orchard_world orchard_husky_headless.launch.py rviz:=false      # RViz2 off

Requires the same one-time symlink setup as orchard_husky.launch.py (see
that file's docstring) -- both launch files spawn into the same registered
'orchard' world slot inside clearpath_gz.

Internally this does NOT include clearpath_gz's simulation.launch.py.
That file has no argument for headless mode -- gz_sim.launch.py (which it
calls) hardcodes the gz_args string with no server-only flag exposed. So
this file instead includes:
  - gz_sim_headless.launch.py (this package's local copy of clearpath_gz's
    gz_sim.launch.py, with a 'headless' argument added)
  - clearpath_gz's robot_spawn.launch.py, unmodified (handles the Husky
    spawn, controllers, and RViz2 -- untouched by the headless change)
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    IncludeLaunchDescription,
    SetEnvironmentVariable,
    DeclareLaunchArgument,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def generate_launch_description():

    pkg_share = get_package_share_directory('orchard_world')

    # So Gazebo can resolve model://citrus_tree inside orchard.sdf
    models_path = os.path.dirname(pkg_share)

    # Where clearpath_gz looks for robot.yaml
    setup_path = os.path.join(pkg_share, 'config')

    # Same registered world slot as orchard_husky.launch.py -- see that
    # file's docstring for the one-time symlink setup this depends on.
    world_name = 'orchard'

    declare_x = DeclareLaunchArgument('x', default_value='-2.0')
    declare_y = DeclareLaunchArgument('y', default_value='2.0')
    declare_yaw = DeclareLaunchArgument('yaw', default_value='0.0')
    declare_rviz = DeclareLaunchArgument('rviz', default_value='true')
    declare_headless = DeclareLaunchArgument('headless', default_value='true')

    set_gz_resource_path = SetEnvironmentVariable(
        name='GZ_SIM_RESOURCE_PATH',
        value=models_path
    )

    gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_share, 'launch', 'gz_sim_headless.launch.py')
        ),
        launch_arguments={
            'world': world_name,
            'setup_path': setup_path,
            'headless': LaunchConfiguration('headless'),
        }.items()
    )

    robot_spawn = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory('clearpath_gz'),
                'launch',
                'robot_spawn.launch.py'
            )
        ),
        launch_arguments={
            'setup_path': setup_path,
            'world': world_name,
            'rviz': LaunchConfiguration('rviz'),
            'x': LaunchConfiguration('x'),
            'y': LaunchConfiguration('y'),
            'yaw': LaunchConfiguration('yaw'),
        }.items()
    )

    return LaunchDescription([
        declare_x,
        declare_y,
        declare_yaw,
        declare_rviz,
        declare_headless,
        set_gz_resource_path,
        gz_sim,
        robot_spawn,
    ])
