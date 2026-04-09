#include "w10_kinematics/arm_angle_ik.hpp"
#include <iostream>
#include <iomanip>

int main() {
  std::string urdf_path = "/home/user/ros2_ws/dynamic_ws/install/w10_sim/share/w10_sim/urdf/w10.urdf";
  w10_kinematics::ArmAngleIK ik(urdf_path);
  
  const auto& model = ik.getModel();
  pinocchio::Data data(model);
  
  std::cout << "\n=== Testing EVERY q index ===" << std::endl;
  
  for (int qi = 0; qi < model.nq; ++qi) {
    Eigen::VectorXd q_test = Eigen::VectorXd::Zero(model.nq);
    q_test(qi) = 0.5;
    
    pinocchio::forwardKinematics(model, data, q_test);
    Eigen::Isometry3d T = Eigen::Isometry3d::Identity();
    int ee_id = model.frames[model.nframes - 1].parent;
    T.linear() = data.oMi[ee_id].rotation();
    T.translation() = data.oMi[ee_id].translation();
    
    double z_change = T.translation()(2) - 0.769802;  // Home Z value
    double xy_magnitude = std::sqrt(T.translation()(0) * T.translation()(0) + 
                                     T.translation()(1) * T.translation()(1));
    
    if (std::abs(z_change) > 1e-6 || xy_magnitude > 1e-6) {
      std::cout << "q[" << qi << "] = 0.5: EE = [" 
                << std::fixed << std::setprecision(6) << T.translation()(0) << ", "
                << T.translation()(1) << ", "
                << T.translation()(2) << "]  *** CHANGES FK ***" << std::endl;
    } else {
      std::cout << "q[" << qi << "] = 0.5: No change" << std::endl;
    }
  }
  
  return 0;
}
