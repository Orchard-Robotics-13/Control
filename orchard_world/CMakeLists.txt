cmake_minimum_required(VERSION 3.8)
project(orchard_world)

find_package(ament_cmake REQUIRED)

install(
  DIRECTORY launch worlds config
  DESTINATION share/${PROJECT_NAME}
)

install(
  DIRECTORY models/
  DESTINATION share
)

# --- Auto-register our world with clearpath_gz -----------------------------
# clearpath_gz's simulation.launch.py only accepts a fixed set of world
# names (construction, office, orchard, pipeline, solar_farm, warehouse) --
# there's no argument to pass an arbitrary world file path. To use our
# world with their robot-spawn machinery, we occupy the 'orchard' slot by
# symlinking over their built-in orchard.sdf with ours.
#
# This runs automatically as part of `colcon build`, using `ros2 pkg prefix`
# to resolve clearpath_gz's install location dynamically -- so it works on
# any machine after a fresh `git clone` + `colcon build`, no manual steps,
# no hardcoded paths.
install(CODE "
  execute_process(
    COMMAND ros2 pkg prefix clearpath_gz
    OUTPUT_VARIABLE CLEARPATH_GZ_PREFIX
    OUTPUT_STRIP_TRAILING_WHITESPACE
    RESULT_VARIABLE CLEARPATH_GZ_FOUND
  )
  if(CLEARPATH_GZ_FOUND EQUAL 0)
    set(TARGET_WORLD \"\${CLEARPATH_GZ_PREFIX}/share/clearpath_gz/worlds/orchard.sdf\")
    set(SOURCE_WORLD \"${CMAKE_INSTALL_PREFIX}/share/orchard_world/worlds/orchard.sdf\")
    file(REMOVE \"\${TARGET_WORLD}\")
    execute_process(
      COMMAND \${CMAKE_COMMAND} -E create_symlink \"\${SOURCE_WORLD}\" \"\${TARGET_WORLD}\"
    )
    message(STATUS \"orchard_world: linked \${TARGET_WORLD} -> \${SOURCE_WORLD}\")
  else()
    message(WARNING \"orchard_world: clearpath_gz not found -- skipping world registration. Build clearpath_gz first, then rebuild orchard_world.\")
  endif()
")

ament_package()
