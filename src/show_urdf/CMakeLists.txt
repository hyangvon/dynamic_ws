cmake_minimum_required(VERSION 3.8)
project(show_urdf)

find_package(ament_cmake REQUIRED)
# Install urdf, launch, config, and meshes directories
install(DIRECTORY launch urdf meshes
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
