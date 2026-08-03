# orchard_world

A Gazebo Harmonic orchard simulation for ROS 2 Jazzy: a 4×10 citrus tree
grid on a flat ground plane, with launch integration for spawning a
Clearpath Husky A300 (Camera with 3D LiDAR disabled) into it via
`clearpath_gz`.

## What's in this repo

```
orchard_world/
├── CMakeLists.txt
├── package.xml
├── launch/
│   ├── orchard_world.launch.py            # trees-only, no robot
│   ├── orchard_husky.launch.py            # trees + Husky A300 spawn
│   └── orchard_husky_headless.launch.py   # trees + Husky, headless Gazebo + RViz2
├── worlds/
│   └── orchard.sdf
├── models/
│   └── citrus_tree/
│       ├── materials/
│           └── textures/aruco_marker_0.png
│       ├── model.sdf
│       └── model.config
└── config/
    └── robot.yaml                  # Husky A300, camera + lidar(disabled)
```

## Prerequisites

- Ubuntu 24.04
- [ROS 2 Jazzy](https://docs.ros.org/en/jazzy/Installation/Ubuntu-Install-Debians.html)
- Gazebo Harmonic (`sudo apt-get install ros-jazzy-ros-gz`)

## Setup from a fresh clone

This package depends on `clearpath_gz` (from Clearpath's `clearpath_simulator`)
for the Husky A300 spawn/control machinery. It needs to be built in the
**same workspace**, and **before** this package, so build both together.

```bash
mkdir -p ~/orchard_ws/src
cd ~/orchard_ws/src

# this package
git clone -b test https://github.com/Orchard-Robotics-13/Control.git orchard_world

# clearpath_simulator_forked (provides forked repo of clearpath_gz)
git clone https://github.com/arslan-da/clearpath_simulator_forked.git

cd ~/orchard_ws
rosdep install -r --from-paths src -i -y
colcon build --symlink-install
source install/setup.bash
```

During the build, you should see a line like:
```
-- orchard_world: linked .../clearpath_gz/share/clearpath_gz/worlds/orchard.sdf -> .../orchard_world/share/orchard_world/worlds/orchard.sdf
```
That confirms `orchard_world`'s `CMakeLists.txt` automatically registered our
world with `clearpath_gz` — no manual steps needed. (See **How the world
integration works** below for why this exists.)

If you ever see a `WARNING` instead saying `clearpath_gz not found`, it means
`clearpath_gz` hadn't finished building yet when `orchard_world` tried to
register its world. Just rebuild:
```bash
colcon build --symlink-install --packages-select orchard_world
```

## Launching

**Trees only, no robot:**
```bash
ros2 launch orchard_world orchard_world.launch.py
```

**Trees + Husky A300 (camera + lidar), Gazebo GUI on:**
```bash
ros2 launch orchard_world orchard_husky.launch.py
```
Optional args: `x`, `y`, `yaw` (spawn pose, default `-2.0 2.0 0.0`), `rviz`
(default `false`).

**Trees + Husky A300, Gazebo headless (server only) + RViz2:**
```bash
ros2 launch orchard_world orchard_husky_headless.launch.py
```
Same `x`, `y`, `yaw` args as above. `rviz` defaults to `true` and
`headless` defaults to `true` here, since that's this file's purpose —
pass `headless:=false` to bring the Gazebo GUI back, or `rviz:=false` to
skip RViz2, without switching files.

Use `orchard_husky.launch.py` while you're still iterating on the world
itself (placing trees, checking marker positions, etc.) — Gazebo's GUI is
the only view that shows the raw authored scene. Switch to
`orchard_husky_headless.launch.py` once you're testing robot
behavior/perception, where RViz2's robot's-eye view (sensor topics, TF,
costmaps) is what actually matters, and the Gazebo render window is just
spending GPU cycles you don't need.

## Notes

- If citrus trees fail to load with `Unable to find uri[model://citrus_tree]`,
  do a clean rebuild (`rm -rf build/orchard_world install/orchard_world`
  then `colcon build`) — this usually means an old install layout is stale.
- `gz_sim_headless.launch.py` imports `ClearpathConfig` from
  `clearpath_config.clearpath_config` in its non-headless code path (same
  as Clearpath's original) — this only matters if you ever run it with
  `headless:=false`; the headless path skips it entirely.
