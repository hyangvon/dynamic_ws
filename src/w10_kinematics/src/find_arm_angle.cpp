#include "w10_kinematics/arm_angle_ik.hpp"
#include <iostream>
#include <iomanip>

int main() {
  try {
    std::string urdf_path = "/home/user/ros2_ws/dynamic_ws/install/w10_sim/share/w10_sim/urdf/w10.urdf";
    w10_kinematics::ArmAngleIK ik_solver(urdf_path);
    int ndof = ik_solver.getNDOF();

    std::cout << "Searching for configurations with different arm angles..." << std::endl;
    std::cout << std::setw(10) << "q2" << std::setw(10) << "q3" << std::setw(10) << "q4" 
              << std::setw(10) << "q5" << std::setw(15) << "Arm Angle (rad)" << std::setw(15) << "Arm Angle (deg)" 
              << std::setw(20) << "EE Pos Z" << std::endl;
    std::cout << std::string(85, '-') << std::endl;

    // Sweep different joint configurations
    for (double q2 = -0.5; q2 <= 0.5; q2 += 0.3) {
      for (double q3 = -0.5; q3 <= 0.5; q3 += 0.3) {
        for (double q4 = -1.0; q4 <= 0.5; q4 += 0.3) {
          for (double q5 = -0.5; q5 <= 1.0; q5 += 0.3) {
            Eigen::VectorXd q = Eigen::VectorXd::Zero(ndof);
            q(2) = q2;
            q(3) = q3;
            q(4) = q4;
            q(5) = q5;

            Eigen::Isometry3d T;
            if (ik_solver.forwardKinematics(q, T)) {
              double arm_angle = ik_solver.getArmAngle(q);
              double arm_angle_deg = arm_angle * 180.0 / M_PI;
              
              std::cout << std::fixed << std::setprecision(2)
                        << std::setw(10) << q2 << std::setw(10) << q3 << std::setw(10) << q4
                        << std::setw(10) << q5 << std::setw(15) << arm_angle 
                        << std::setw(15) << arm_angle_deg << std::setw(20) << T.translation()(2) << std::endl;
            }
          }
        }
      }
    }

  } catch (const std::exception& e) {
    std::cerr << "Exception: " << e.what() << std::endl;
    return 1;
  }

  return 0;
}
