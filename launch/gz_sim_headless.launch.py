"""
Local copy of clearpath_gz's gz_sim.launch.py, with one addition: a
'headless' launch argument that appends '-s' to gz_args when true,
running the Gazebo server only (no GUI render window).

This exists as a local copy -- rather than a patch to the installed
clearpath_gz package -- because gz_sim.launch.py hardcodes its gz_args
string with no argument exposed for headless/server-only mode, and any
in-place edit to the installed package would be overwritten on the next
colcon build / reinstall of clearpath_simulator.

Everything else (robot spawn, controllers, RViz2) is untouched and still
comes directly from clearpath_gz's own robot_spawn.launch.py -- only the
Gazebo-launching piece is replaced.
"""

import os
import tempfile

from ament_index_python.packages import get_package_share_directory
from clearpath_config.clearpath_config import ClearpathConfig

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.actions import IncludeLaunchDescription, SetEnvironmentVariable
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import EnvironmentVariable, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node


ARGUMENTS = [
    DeclareLaunchArgument('use_sim_time', default_value='true',
                           choices=['true', 'false'],
                           description='use_sim_time'),
    DeclareLaunchArgument('world', default_value='warehouse',
                           description='Gazebo World'),
    DeclareLaunchArgument('auto_start', default_value='true',
                           choices=['true', 'false'],
                           description='Auto-start Gazebo simulation'),
    DeclareLaunchArgument('setup_path',
                           default_value=[EnvironmentVariable('HOME'), '/clearpath/'],
                           description='Clearpath setup path'),
    # --- addition vs. clearpath_gz's original gz_sim.launch.py ---
    DeclareLaunchArgument('headless', default_value='false',
                           choices=['true', 'false'],
                           description='Run Gazebo server only, no GUI render window'),
]


def gz_launch(context, *args, **kwargs):

    # Directories
    pkg_clearpath_gz = get_package_share_directory('clearpath_gz')
    pkg_ros_gz_sim = get_package_share_directory('ros_gz_sim')

    # Paths
    gz_sim_launch = PathJoinSubstitution(
        [pkg_ros_gz_sim, 'launch', 'gz_sim.launch.py'])

    static_gui_config = os.path.join(pkg_clearpath_gz, 'config', 'gui.config')

    headless = LaunchConfiguration('headless').perform(context)
    headless_option = ' -s' if headless == 'true' else ''

    auto_start_option = ''
    auto_start = LaunchConfiguration('auto_start').perform(context)
    if auto_start == 'true':
        auto_start_option = ' -r'

    if headless == 'true':
        # No GUI window will open, so there's no gui.config to patch or pass.
        gz_args = [
            LaunchConfiguration('world'),
            '.sdf',
            auto_start_option,
            ' -v 4',
            headless_option,
        ]
    else:
        # Same behaviour as clearpath_gz's original file: patch the
        # teleop topic into the GUI config based on robot.yaml's namespace.
        setup_path = LaunchConfiguration('setup_path').perform(context)
        robot_yaml = os.path.join(setup_path, 'robot.yaml')
        if os.path.isfile(robot_yaml):
            clearpath_config = ClearpathConfig(robot_yaml)
            namespace = clearpath_config.system.namespace
            topic = f'/{namespace}/cmd_vel' if namespace not in ('', '/') else '/cmd_vel'
            with open(static_gui_config) as f:
                content = f.read()
            content = content.replace(
                '<plugin filename="Teleop">',
                f'<plugin filename="Teleop">\n      <topic>{topic}</topic>'
            )
            tmp = tempfile.NamedTemporaryFile(suffix='.config', delete=False, mode='w')
            tmp.write(content)
            tmp.close()
            gui_config = tmp.name
        else:
            gui_config = static_gui_config

        gz_args = [
            LaunchConfiguration('world'),
            '.sdf',
            auto_start_option,
            ' -v 4',
            ' --gui-config ',
            gui_config,
        ]

    gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([gz_sim_launch]),
        launch_arguments=[('gz_args', gz_args)]
    )

    return [gz_sim]


def generate_launch_description():

    pkg_clearpath_gz = get_package_share_directory('clearpath_gz')

    packages_paths = [os.path.join(p, 'share') for p in os.getenv('AMENT_PREFIX_PATH').split(':')]

    gz_sim_resource_path = SetEnvironmentVariable(
        name='GZ_SIM_RESOURCE_PATH',
        value=[
            os.path.join(pkg_clearpath_gz, 'worlds') + ':',
            os.path.join(pkg_clearpath_gz, 'meshes') + ':',
            ':' + ':'.join(packages_paths)])

    clock_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        name='clock_bridge',
        output='screen',
        arguments=['/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock']
    )

    ld = LaunchDescription(ARGUMENTS)
    ld.add_action(gz_sim_resource_path)
    ld.add_action(OpaqueFunction(function=gz_launch))
    ld.add_action(clock_bridge)
    return ld
