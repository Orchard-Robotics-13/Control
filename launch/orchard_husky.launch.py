"""
Launches the orchard world (citrus tree grid, flat ground) and spawns a
Clearpath Husky A300 (camera + 3D lidar, via clearpath_gz) into it.

Usage:
  ros2 launch orchard_world orchard_husky.launch.py

Expected package layout:

  orchard_world/
  ├── worlds/orchard.sdf
  ├── models/citrus_tree/{model.sdf, model.config}
  └── config/robot.yaml

One-time setup before this will work -- clearpath_gz only looks inside its
own package's worlds/ folder, so symlink orchard.sdf in under a distinct
name (avoids colliding with clearpath_gz's own built-in 'orchard' demo world):

  ln -s $(ros2 pkg prefix orchard_world)/share/orchard_world/worlds/orchard.sdf \\
        $(ros2 pkg prefix clearpath_gz)/share/clearpath_gz/worlds/orchard_custom.sdf
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
    models_path = os.path.join(pkg_share, 'models')

    # Where clearpath_gz looks for robot.yaml
    setup_path = os.path.join(pkg_share, 'config')

    # clearpath_gz's launch file only accepts a fixed set of world names
    # (construction, office, orchard, pipeline, solar_farm, warehouse).
    # We overwrite the 'orchard' symlink in clearpath_gz's worlds folder
    # to point at OUR orchard.sdf instead of theirs -- see setup step above.
    world_name = 'orchard'

    declare_x = DeclareLaunchArgument('x', default_value='-2.0')
    declare_y = DeclareLaunchArgument('y', default_value='2.0')
    declare_yaw = DeclareLaunchArgument('yaw', default_value='0.0')
    declare_rviz = DeclareLaunchArgument('rviz', default_value='false')

    set_gz_resource_path = SetEnvironmentVariable(
        name='GZ_SIM_RESOURCE_PATH',
        value=models_path
    )

    clearpath_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory('clearpath_gz'),
                'launch',
                'simulation.launch.py'
            )
        ),
        launch_arguments={
            'setup_path': setup_path,
            'world': world_name,
            'x': LaunchConfiguration('x'),
            'y': LaunchConfiguration('y'),
            'yaw': LaunchConfiguration('yaw'),
            'rviz': LaunchConfiguration('rviz'),
        }.items()
    )

    return LaunchDescription([
        declare_x,
        declare_y,
        declare_yaw,
        declare_rviz,
        set_gz_resource_path,
        clearpath_sim,
    ])