#include "w10_kinematics/arm_angle_ik.hpp"
#include <iostream>
#include <iomanip>

int main() {
  try {
    std::string urdf_path = "/home/user/ros2_ws/dynamic_ws/install/w10_sim/share/w10_sim/urdf/w10.urdf";
    w10_kinematics::ArmAngleIK ik_solver(urdf_path);
    int ndof = ik_solver.getNDOF();

    std::cout << "\n=== Debugging Shoulder and Wrist Positions ===" << std::endl;
    
    // Test with zero config
    {
      std::cout << "\n--- Zero Config ---" << std::endl;
      Eigen::VectorXd q = Eigen::VectorXd::Zero(ndof);
      Eigen::Isometry3d T;
      ik_solver.forwardKinematics(q, T);
      
      std::cout << "Joint config: all zeros" << std::endl;
      std::cout << "EE Position: " << T.translation().transpose() << std::endl;
      std::cout << "Arm Angle: " << ik_solver.getArmAngle(q) * 180 / M_PI << " deg" << std::endl;
    }

    // Test with different q2 values
    {
      std::cout << "\n--- Varying q2 (shoulder roll) ---" << std::endl;
      for (double q2 = -0.5; q2 <= 0.5; q2 += 0.25) {
        Eigen::VectorXd q = Eigen::VectorXd::Zero(ndof);
        q(2) = q2;
        Eigen::Isometry3d T;
        ik_solver.forwardKinematics(q, T);
        
        std::cout << "q2=" << std::fixed << std::setprecision(2) << q2 
                  << " -> EE Pos: (" << T.translation().transpose().format(Eigen::IOFormat(Eigen::StreamPrecision, 0, ", ", ", ", "", "", "[", "]")) 
                  << ") Arm Angle: " << ik_solver.getArmAngle(q) * 180 / M_PI << " deg" << std::endl;
      }
    }

    // Test with large q4 values to move the arm more
    {
      std::cout << "\n--- Varying q4 with fixed q2=-0.5 ---" << std::endl;
      for (double q4 = -1.5; q4 <= 0.5; q4 += 0.3) {
        Eigen::VectorXd q = Eigen::VectorXd::Zero(ndof);
        q(2) = -0.5;
        q(4) = q4;
        Eigen::Isometry3d T;
        ik_solver.forwardKinematics(q, T);
        
        std::cout << "q2=-0.50, q4=" << std::fixed << std::setprecision(2) << q4 
                  << " -> EE Pos: (" << T.translation().transpose().format(Eigen::IOFormat(Eigen::StreamPrecision, 0, ", ", ", ", "", "", "[", "]")) 
                  << ") Arm Angle: " << ik_solver.getArmAngle(q) * 180 / M_PI << " deg" << std::endl;
      }
    }

  } catch (const std::exception& e) {
    std::cerr << "Exception: " << e.what() << std::endl;
    return 1;
  }

  return 0;
}
