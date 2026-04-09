#include "w10_kinematics/arm_angle_ik.hpp"
#include <iostream>
#include <iomanip>

int main() {
  std::string urdf_path = "/home/user/ros2_ws/dynamic_ws/install/w10_sim/share/w10_sim/urdf/w10.urdf";
  w10_kinematics::ArmAngleIK ik(urdf_path);
  
  const auto& model = ik.getModel();
  pinocchio::Data data(model);
  
  std::cout << "\n=== Detailed Q Vector Analysis ===" << std::endl;
  std::cout << "Total nq: " << model.nq << ", Total nv: " << model.nv << std::endl;
  
  // Print each joint's nq offset
  std::cout << "\n=== Joint nq/nv Details ===" << std::endl;
  std::cout << std::left << std::setw(15) << "Joint" << std::setw(10) << "nq" 
            << std::setw(10) << "nv" << std::setw(15) << "q_offset" << std::endl;
  std::cout << std::string(50, '-') << std::endl;
  
  int q_offset = 0;
  for (size_t i = 0; i < model.joints.size(); ++i) {
    std::string name = model.names[i];
    int nq = model.joints[i].nq();
    int nv = model.joints[i].nv();
    std::cout << std::left << std::setw(15) << name << std::setw(10) << nq 
              << std::setw(10) << nv << std::setw(15) << q_offset << std::endl;
    q_offset += nq;
  }
  
  std::cout << "\n=== Testing individual joints ===" << std::endl;
  
  // Test each joint individually
  std::vector<std::pair<std::string, int>> joints_to_test = {
    {"joint2", 1},
    {"joint3", 3},
    {"joint4", 4},  // or maybe 5?
    {"joint5", 6},
    {"joint6", 7},
    {"joint7", 9},
    {"joint8", 10}
  };
  
  for (const auto& joint : joints_to_test) {
    Eigen::VectorXd q_test = Eigen::VectorXd::Zero(model.nq);
    q_test(joint.second) = 0.3;
    
    pinocchio::forwardKinematics(model, data, q_test);
    Eigen::Isometry3d T = Eigen::Isometry3d::Identity();
    int ee_id = model.frames[model.nframes - 1].parent;
    T.linear() = data.oMi[ee_id].rotation();
    T.translation() = data.oMi[ee_id].translation();
    
    std::cout << "q[" << joint.second << "] = 0.3 (" << joint.first << "): [" 
              << T.translation()(0) << ", " 
              << T.translation()(1) << ", "
              << T.translation()(2) << "]" << std::endl;
  }
  
  return 0;
}
