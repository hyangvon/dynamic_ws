cmake_minimum_required(VERSION 3.8)
project(w10_kinematics)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# find dependencies
find_package(ament_cmake_auto REQUIRED)
ament_auto_find_build_dependencies()

find_package(Eigen3 REQUIRED NO_MODULE)
find_package(pinocchio REQUIRED)
find_package(w10_sim REQUIRED)
find_package(rclcpp REQUIRED)
find_package(sensor_msgs REQUIRED)

# Include directories
include_directories(include)

# Create library
add_library(arm_angle_ik src/arm_angle_ik.cpp)
target_link_libraries(arm_angle_ik
  Eigen3::Eigen
  pinocchio::pinocchio
)
target_include_directories(arm_angle_ik PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include>
)

# Build executables
add_executable(ik_test src/ik_test.cpp)
target_link_libraries(ik_test
  arm_angle_ik
  Eigen3::Eigen
  pinocchio::pinocchio
)

add_executable(find_arm_angle src/find_arm_angle.cpp)
target_link_libraries(find_arm_angle
  arm_angle_ik
  Eigen3::Eigen
  pinocchio::pinocchio
)

add_executable(debug_positions src/debug_positions.cpp)
target_link_libraries(debug_positions
  arm_angle_ik
  Eigen3::Eigen
  pinocchio::pinocchio
)

add_executable(debug_joints src/debug_joints.cpp)
target_link_libraries(debug_joints
  arm_angle_ik
  Eigen3::Eigen
  pinocchio::pinocchio
)

add_executable(debug_q_mapping src/debug_q_mapping.cpp)
target_link_libraries(debug_q_mapping
  arm_angle_ik
  Eigen3::Eigen
  pinocchio::pinocchio
)

add_executable(test_q_indices src/test_q_indices.cpp)
target_link_libraries(test_q_indices
  arm_angle_ik
  Eigen3::Eigen
  pinocchio::pinocchio
)

add_executable(test_all_q src/test_all_q.cpp)
target_link_libraries(test_all_q
  arm_angle_ik
  Eigen3::Eigen
  pinocchio::pinocchio
)

add_executable(ik_visualize src/ik_visualize.cpp)
target_link_libraries(ik_visualize
  arm_angle_ik
  Eigen3::Eigen
  pinocchio::pinocchio
)
ament_target_dependencies(ik_visualize
  rclcpp
  sensor_msgs
)

# Install library
install(TARGETS arm_angle_ik
  LIBRARY DESTINATION lib
  ARCHIVE DESTINATION lib
)

# Install headers
install(DIRECTORY include/
  DESTINATION include
)

# Install launch files
install(DIRECTORY launch/
  DESTINATION share/${PROJECT_NAME}/launch
)

# Install executables
install(TARGETS ik_test ik_visualize debug_joints debug_q_mapping test_q_indices test_all_q debug_positions find_arm_angle
  DESTINATION lib/${PROJECT_NAME}
)

ament_package()
