cmake_minimum_required(VERSION 3.8)
project(w10_moveit_kinematics)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(ament_cmake_python REQUIRED)
find_package(rclpy REQUIRED)

# Install Python package
ament_python_install_package(kinematics_experiments)

# Install Python scripts
install(PROGRAMS
  kinematics_experiments/scripts/forward_kinematics_demo.py
  kinematics_experiments/scripts/inverse_kinematics_demo.py
  kinematics_experiments/scripts/motion_planning_demo.py
  kinematics_experiments/scripts/interactive_kinematics.py
  kinematics_experiments/scripts/joint_state_publisher.py
  DESTINATION lib/${PROJECT_NAME}
)

# Install launch and config files
install(DIRECTORY
  w10_moveit_config/launch
  w10_moveit_config/config
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
