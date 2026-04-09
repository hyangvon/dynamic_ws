#include "w10_kinematics/arm_angle_ik.hpp"
#include <iostream>
#include <iomanip>

int main() {
  std::string urdf_path = "/home/user/ros2_ws/dynamic_ws/install/w10_sim/share/w10_sim/urdf/w10.urdf";
  w10_kinematics::ArmAngleIK ik(urdf_path);
  
  const auto& model = ik.getModel();
  
  std::cout << "\n=== Q Vector Structure ===" << std::endl;
  std::cout << "Total nq: " << model.nq << std::endl;
  std::cout << "Active DOF (nv): " << model.nv << std::endl;
  
  // Print mapping between q indices and joints
  std::cout << "\n=== Q Index to Joint Mapping ===" << std::endl;
  std::cout << std::left << std::setw(5) << "q[i]" << std::setw(20) << "Joint" << std::setw(30) << "Description" << std::endl;
  std::cout << std::string(55, '-') << std::endl;
  
  int q_idx = 0;
  for (size_t j = 0; j < model.joints.size(); ++j) {
    int nq_this = model.joints[j].nq();
    int nv_this = model.joints[j].nv();
    std::string joint_name = model.names[j];
    std::string desc;
    
    if (joint_name == "universe") {
      desc = "Free flyer (quaternion+pos)";
    } else if (joint_name.find("joint") != std::string::npos) {
      desc = "Revolute";
    }
    
    std::cout << std::left << std::setw(5) << q_idx << std::setw(20) << joint_name 
              << std::setw(30) << desc << " (nq=" << nq_this << ", nv=" << nv_this << ")" << std::endl;
    
    for (int i = 1; i < nq_this; ++i) {
      std::cout << std::left << std::setw(5) << (q_idx + i) << "" << std::endl;
    }
    
    q_idx += nq_this;
  }
  
  std::cout << "\n=== Testing FK with perturbed joints ===" << std::endl;
  
  // Test configuration: home position
  Eigen::VectorXd q_home = Eigen::VectorXd::Zero(model.nq);
  Eigen::Isometry3d T_home;
  ik.forwardKinematics(q_home, T_home);
  std::cout << "Home position (all zeros): [" 
            << T_home.translation()(0) << ", "
            << T_home.translation()(1) << ", "
            << T_home.translation()(2) << "]" << std::endl;
  
  // Test: perturb joint2 (q_idx should be 4 for joint2)
  Eigen::VectorXd q_test1 = Eigen::VectorXd::Zero(model.nq);
  q_test1(1) = 0.5;  // universe (quaternion x)
  Eigen::Isometry3d T_test1;
  ik.forwardKinematics(q_test1, T_test1);
  std::cout << "With q[1] = 0.5: [" 
            << T_test1.translation()(0) << ", "
            << T_test1.translation()(1) << ", "
            << T_test1.translation()(2) << "]" << std::endl;
  
  // Test: perturb what we think is joint2
  Eigen::VectorXd q_test2 = Eigen::VectorXd::Zero(model.nq);
  q_test2(4) = 0.5;  // Assuming joint2 is at index 4
  Eigen::Isometry3d T_test2;
  ik.forwardKinematics(q_test2, T_test2);
  std::cout << "With q[4] = 0.5: [" 
            << T_test2.translation()(0) << ", "
            << T_test2.translation()(1) << ", "
            << T_test2.translation()(2) << "]" << std::endl;
  
  std::cout << "\n";
  
  return 0;
}
