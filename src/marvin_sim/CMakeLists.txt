cmake_minimum_required(VERSION 3.8)
project(marvin_sim)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# find dependencies
find_package(ament_cmake_auto REQUIRED)
ament_auto_find_build_dependencies()

find_package(sensor_msgs REQUIRED)

# Special handling for Eigen3 as it's often header-only
find_package(Eigen3 REQUIRED NO_MODULE)
include_directories(${EIGEN3_INCLUDE_DIRS})

# Build executables
ament_auto_add_executable(ctsvi_node src/ctsvi_node.cpp)
ament_target_dependencies(ctsvi_node sensor_msgs)
ament_auto_add_executable(atsvi_node src/atsvi_node.cpp)
ament_auto_add_executable(c_atsvi_node src/c_atsvi_node.cpp)

install(DIRECTORY launch urdf meshes config
  DESTINATION share/${PROJECT_NAME}
)

install(PROGRAMS
        scripts/vi_sim.py
        scripts/analyze_vi_results.py
        scripts/replay_rviz.py
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

ament_auto_package()
