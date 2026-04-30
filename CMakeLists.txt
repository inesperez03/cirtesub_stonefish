cmake_minimum_required(VERSION 3.5)
project(cirtesub_stonefish)

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(std_msgs REQUIRED)
find_package(stonefish_ros2 REQUIRED) 

# Asegúrate de que esté habilitado el soporte para C
enable_language(C)

# Include directories
include_directories(
  include
  ${std_msgs_INCLUDE_DIRS}
  ${stonefish_ros2_INCLUDE_DIRS}  # Add this line
)

# Agregar el directorio para el código Python
set(PYTHON_EXECUTABLE /usr/bin/python3)  # Asegúrate de que esta ruta sea correcta

# Instalar el script de Python
install(
  PROGRAMS
    scripts/odom2tf.py
    scripts/battery_status_simulated.py
    scripts/leak_sensors_simulated.py
    scripts/pressure_to_pose.py
    scripts/dvl_to_twist.py
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
