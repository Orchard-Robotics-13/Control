cmake_minimum_required(VERSION 3.8)
project(assignment2)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# find dependencies
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(std_msgs REQUIRED)
find_package(tf2 REQUIRED)
find_package(tf2_ros REQUIRED)
find_package(nav_msgs REQUIRED)
# Include the header files directory
include_directories(include)

# 1. Build the Fleet Controller Node (Linking the Audi physics to the main node)
add_executable(fleet_controller_node 
  src/fleet_controller.cpp 
  src/audi_car.cpp
  src/husky.cpp
)
ament_target_dependencies(fleet_controller_node rclcpp geometry_msgs std_msgs tf2 tf2_ros nav_msgs)

# 2. Build the Mission Planner Node
add_executable(mission_planner_node src/mission_planner.cpp)
ament_target_dependencies(mission_planner_node rclcpp geometry_msgs)

# 3. Tell ROS 2 where to install the compiled executables
install(TARGETS
  fleet_controller_node
  mission_planner_node
  DESTINATION lib/${PROJECT_NAME}
)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  # the following line skips the linter which checks for copyrights
  # comment the line when a copyright and license is added to all source files
  set(ament_cmake_copyright_FOUND TRUE)
  # the following line skips cpplint (only works in a git repo)
  # comment the line when this package is in a git repo and when
  # a copyright and license is added to all source files
  set(ament_cmake_cpplint_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
