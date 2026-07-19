"""
Launches the orchard world (citrus tree grid, flat ground) in Gazebo Harmonic.
No robot spawn -- just the environment.

Usage:
  ros2 launch orchard_world orchard_world.launch.py

Expects this package layout (installed via CMakeLists.txt's
install(DIRECTORY worlds models DESTINATION share/${PROJECT_NAME})):

  orchard_world/
  ├── worlds/orchard.sdf
  └── models/citrus_tree/{model.sdf, model.config}
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, SetEnvironmentVariable
from launch.launch_description_sources import PythonLaunchDescriptionSource


def generate_launch_description():

    pkg_share = get_package_share_directory('orchard_world')

    world_path = os.path.join(pkg_share, 'worlds', 'orchard.sdf')

    # models/ now installs to share/ root (not share/orchard_world/models) --
    # see CMakeLists.txt -- so citrus_tree sits at pkg_share's parent directory
    models_path = os.path.dirname(pkg_share)

    # So Gazebo can resolve model://citrus_tree inside orchard.sdf
    set_resource_path = SetEnvironmentVariable(
        name='GZ_SIM_RESOURCE_PATH',
        value=models_path
    )

    gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory('ros_gz_sim'),
                'launch',
                'gz_sim.launch.py'
            )
        ),
        launch_arguments={'gz_args': world_path}.items()
    )

    return LaunchDescription([
        set_resource_path,
        gz_sim,
    ])
