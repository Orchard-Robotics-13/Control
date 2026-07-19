# orchard_world

A Gazebo Harmonic orchard simulation for ROS 2 Jazzy: a 4×10 citrus tree
grid on a flat ground plane, with launch integration for spawning a
Clearpath Husky A300 (dual camera + Ouster 3D lidar) into it via
`clearpath_gz`.

## What's in this repo

```
orchard_world/
├── CMakeLists.txt
├── package.xml
├── dependencies.repos
├── launch/
│   ├── orchard_world.launch.py    # trees-only, no robot
│   └── orchard_husky.launch.py    # trees + Husky A300 spawn
├── worlds/
│   └── orchard.sdf
├── models/
│   └── citrus_tree/
│       ├── model.sdf
│       └── model.config
└── config/
    └── robot.yaml                  # Husky A300, camera + lidar
```

## Prerequisites

- Ubuntu 24.04
- [ROS 2 Jazzy](https://docs.ros.org/en/jazzy/Installation/Ubuntu-Install-Debians.html)
- Gazebo Harmonic (`sudo apt-get install ros-jazzy-ros-gz`)

## Setup from a fresh clone

This package depends on `clearpath_gz` (from Clearpath's `clearpath_simulator`)
for the Husky A300 spawn/control machinery. It needs to be built in the
**same workspace**, and **before** this package, so build both together.
`dependencies.repos` pins the exact `clearpath_simulator` commit this
package was built and tested against.

```bash
mkdir -p ~/orchard_ws/src
cd ~/orchard_ws/src

# this package (lives on the 'world' branch of the team repo)
git clone -b world https://github.com/Orchard-Robotics-13/Control.git orchard_world

# pinned clearpath_simulator (provides clearpath_gz)
sudo apt install python3-vcstool
vcs import . < orchard_world/dependencies.repos

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

**Trees + Husky A300 (camera + lidar):**
```bash
ros2 launch orchard_world orchard_husky.launch.py
```
Optional args: `x`, `y`, `yaw` (spawn pose, default `-2.0 2.0 0.0`), `rviz`
(default `false`).

## How the world integration works

`clearpath_gz`'s launch file only accepts a fixed set of built-in world names
(`construction`, `office`, `orchard`, `pipeline`, `solar_farm`, `warehouse`) —
there's no argument to point it at an arbitrary world file. To use our world
with their robot-spawn machinery, `orchard_world`'s `CMakeLists.txt`
automatically symlinks our `orchard.sdf` over their built-in `orchard` world
slot as part of every `colcon build`. This is driven entirely by
`ros2 pkg prefix` at build time — nothing is hardcoded to a specific
machine or username, so it reproduces identically for anyone who clones this
repo and builds it.

## Notes

- `config/robot.yaml`'s Axis PTZ camera and Fixposition INS entries are
  real-hardware-only (no Gazebo plugin) — they won't produce data in sim.
  Safe to delete if they ever cause build errors.
- If citrus trees fail to load with `Unable to find uri[model://citrus_tree]`,
  do a clean rebuild (`rm -rf build/orchard_world install/orchard_world`
  then `colcon build`) — this usually means an old install layout is stale.
