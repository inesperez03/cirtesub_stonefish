cmake_minimum_required(VERSION 3.5)
project(cirtesub_stonefish)

if(NOT CMAKE_CXX_STANDARD)
  set(CMAKE_CXX_STANDARD 17)
endif()
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(std_msgs REQUIRED)
find_package(sura_msgs REQUIRED)
find_package(stonefish_ros2 REQUIRED) 

add_executable(dvl_to_twist_node src/dvl_to_twist_node.cpp)
ament_target_dependencies(
  dvl_to_twist_node
  rclcpp
  geometry_msgs
  stonefish_ros2
)

add_executable(battery_status_simulated src/battery_status_simulated.cpp)
ament_target_dependencies(
  battery_status_simulated
  rclcpp
  sensor_msgs
  std_msgs
)

add_executable(leak_sensors_simulated src/leak_sensors_simulated.cpp)
ament_target_dependencies(
  leak_sensors_simulated
  rclcpp
  sura_msgs
)

install(
  TARGETS
    dvl_to_twist_node
    battery_status_simulated
    leak_sensors_simulated
  DESTINATION lib/${PROJECT_NAME}
)

# Install launch files
install(DIRECTORY launch
  DESTINATION share/${PROJECT_NAME}/
)

# Install data and scenarios folders
install(DIRECTORY data scenarios
  DESTINATION share/${PROJECT_NAME}
)

install(DIRECTORY urdf
  DESTINATION share/${PROJECT_NAME}
)

install(DIRECTORY resources
  DESTINATION share/${PROJECT_NAME}
)

install(DIRECTORY config
  DESTINATION share/${PROJECT_NAME}
)


# Enable testing and install test files
if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
