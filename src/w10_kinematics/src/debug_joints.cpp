#include "w10_kinematics/arm_angle_ik.hpp"
#include <iostream>
#include <iomanip>

int main() {
  std::string urdf_path = "/home/user/ros2_ws/dynamic_ws/install/w10_sim/share/w10_sim/urdf/w10.urdf";
  w10_kinematics::ArmAngleIK ik(urdf_path);
  
  const auto& model = ik.getModel();
  
  std::cout << "\n=== Pinocchio Model Structure ===" << std::endl;
  std::cout << "Total DOF (nq): " << model.nq << std::endl;
  std::cout << "Total bodies (nbodies): " << model.nbodies << std::endl;
  std::cout << "Total joints (njoints): " << model.njoints << std::endl;
  std::cout << "Total frames (nframes): " << model.nframes << std::endl;
  
  std::cout << "\n=== Joint Names and Indices ===" << std::endl;
  std::cout << std::left << std::setw(5) << "Idx" << std::setw(20) << "Name" << std::setw(10) << "nv" << std::endl;
  std::cout << std::string(35, '-') << std::endl;
  for (size_t i = 0; i < model.joints.size(); ++i) {
    std::cout << std::left << std::setw(5) << i << std::setw(20) << model.names[i] << std::setw(10) << model.joints[i].nv() << std::endl;
  }
  
  std::cout << "\n=== Frame Names ===" << std::endl;
  std::cout << std::left << std::setw(5) << "Idx" << std::setw(30) << "Name" << std::setw(10) << "Parent" << std::endl;
  std::cout << std::string(45, '-') << std::endl;
  for (size_t i = 0; i < model.frames.size(); ++i) {
    std::cout << std::left << std::setw(5) << i << std::setw(30) << model.frames[i].name << std::setw(10) << model.frames[i].parent << std::endl;
  }
  
  std::cout << "\n=== Active Joints (nv > 0) ===" << std::endl;
  std::vector<std::string> active_joints = ik.getJointNames();
  for (size_t i = 0; i < active_joints.size(); ++i) {
    std::cout << "  [" << i << "] " << active_joints[i] << std::endl;
  }
  
  return 0;
}
