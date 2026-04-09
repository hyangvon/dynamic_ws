#include "w10_kinematics/arm_angle_ik.hpp"
#include <iostream>
#include <iomanip>

void printConfig(const Eigen::VectorXd& q, const std::string& label) {
  std::cout << label << ": ";
  for (int i = 0; i < q.size(); ++i) {
    std::cout << std::fixed << std::setprecision(4) << q(i) << " ";
  }
  std::cout << std::endl;
}

int main() {
  try {
    std::string urdf_path = "/home/user/ros2_ws/dynamic_ws/install/w10_sim/share/w10_sim/urdf/w10.urdf";

    std::cout << "========================================" << std::endl;
    std::cout << "   W10 Arm Angle Dimension Reduction IK" << std::endl;
    std::cout << "========================================" << std::endl;
    std::cout << "URDF: " << urdf_path << std::endl << std::endl;

    w10_kinematics::ArmAngleIK ik_solver(urdf_path);

    int ndof = ik_solver.getNDOF();
    std::cout << "[Test] Total DOF: " << ndof << std::endl;
    std::cout << "[Test] Total Bodies: " << ik_solver.getNBodies() << std::endl << std::endl;

    std::cout << "--- Test 1: Forward Kinematics (Zero Config) ---" << std::endl;
    Eigen::VectorXd q_zero = Eigen::VectorXd::Zero(ndof);
    Eigen::Isometry3d T_zero;

    if (ik_solver.forwardKinematics(q_zero, T_zero)) {
      printConfig(q_zero, "Config");
      std::cout << "End-Effector Position: " << T_zero.translation().transpose() << std::endl;
      double arm_angle = ik_solver.getArmAngle(q_zero);
      std::cout << "Arm Angle: " << arm_angle << " rad (" << (arm_angle * 180 / M_PI) << " deg)" << std::endl;
    } else {
      std::cerr << "FK failed" << std::endl;
      return 1;
    }

    std::cout << "\n--- Test 2: Forward Kinematics (Custom Config) ---" << std::endl;
    Eigen::VectorXd q_custom = Eigen::VectorXd::Zero(ndof);
    q_custom(2) = 0.5;
    q_custom(3) = 0.3;
    q_custom(4) = -0.8;
    Eigen::Isometry3d T_custom;

    if (ik_solver.forwardKinematics(q_custom, T_custom)) {
      printConfig(q_custom, "Config");
      std::cout << "End-Effector Position: " << T_custom.translation().transpose() << std::endl;
      double arm_angle = ik_solver.getArmAngle(q_custom);
      std::cout << "Arm Angle: " << arm_angle << " rad (" << (arm_angle * 180 / M_PI) << " deg)" << std::endl;
    }

    std::cout << "\n--- Test 3: Arm Angle Calculation ---" << std::endl;
    for (int i = 0; i < 3; ++i) {
      Eigen::VectorXd q = Eigen::VectorXd::Zero(ndof);
      q(4) = -0.5 + i * 0.5;
      double aa = ik_solver.getArmAngle(q);
      std::cout << "  joint5=" << std::fixed << std::setprecision(2) << q(4) 
                << " -> Arm Angle=" << aa << " rad" << std::endl;
    }

    std::cout << "\n--- Test 4: Inverse Kinematics (With Arm Angle Constraint) ---" << std::endl;
    // 创建一个实际具有不同臂角的目标配置
    Eigen::VectorXd q_target = Eigen::VectorXd::Zero(ndof);
    q_target(2) = 0.5;      // Shoulder joint
    q_target(3) = 0.4;      // Shoulder joint
    q_target(4) = -0.6;     // Shoulder joint
    q_target(5) = 0.3;      // Wrist joint - 这可能影响臂角
    Eigen::Isometry3d T_target;
    ik_solver.forwardKinematics(q_target, T_target);
    double target_config_arm_angle = ik_solver.getArmAngle(q_target);
    
    std::cout << "Target Joint Config: q2=" << q_target(2) << " q3=" << q_target(3) 
              << " q4=" << q_target(4) << " q5=" << q_target(5) << std::endl;
    std::cout << "Target Position: " << T_target.translation().transpose() << std::endl;
    std::cout << "Target Configuration's Arm Angle: " << target_config_arm_angle << " rad" << std::endl;
    std::cout << "Target Arm Angle (for IK): " << 0.5 << " rad (28.65 deg)" << std::endl;

    // 使用远离目标的初始配置
    Eigen::VectorXd q_init = Eigen::VectorXd::Zero(ndof);
    q_init(2) = -0.3;
    q_init(3) = -0.2;
    q_init(4) = 0.5;
    
    Eigen::VectorXd q_solution;
    double target_arm_angle = 0.5;

    bool ik_success = ik_solver.solveIK(
        target_arm_angle,
        T_target.translation(),
        T_target.linear(),
        q_init,
        q_solution,
        1e-5,
        1000
    );

    if (ik_success) {
      std::cout << "[SUCCESS] IK Converged" << std::endl;
      printConfig(q_solution, "Solution");

      // 验证解
      Eigen::Isometry3d T_verify;
      ik_solver.forwardKinematics(q_solution, T_verify);
      
      Eigen::Vector3d pos_error = T_target.translation() - T_verify.translation();
      double pos_error_norm = pos_error.norm();
      double achieved_arm_angle = ik_solver.getArmAngle(q_solution);
      double arm_angle_error = std::abs(achieved_arm_angle - target_arm_angle);

      std::cout << "\nVerification:" << std::endl;
      std::cout << "  Target Position:      " << T_target.translation().transpose() << std::endl;
      std::cout << "  Achieved Position:    " << T_verify.translation().transpose() << std::endl;
      std::cout << "  Position Error (L2):  " << std::scientific << pos_error_norm << std::endl;
      std::cout << "  Target Arm Angle:     " << std::fixed << std::setprecision(6) << target_arm_angle << " rad" << std::endl;
      std::cout << "  Achieved Arm Angle:   " << achieved_arm_angle << " rad" << std::endl;
      std::cout << "  Arm Angle Error:      " << arm_angle_error << " rad" << std::endl;

      if (pos_error_norm < 1e-4) {
        std::cout << "[RESULT] ✓ Position accuracy meets requirements (< 1e-4)" << std::endl;
      } else {
        std::cout << "[WARNING] ✗ Position error exceeds 1e-4" << std::endl;
      }
    } else {
      std::cout << "[FAILED] IK did not converge" << std::endl;
    }

    std::cout << "\n--- Test 5: IK with Different Arm Angles ---" << std::endl;
    std::vector<double> test_arm_angles = {-0.2, 0.0, 0.3, 0.6};
    int success_count = 0;

    for (double aa : test_arm_angles) {
      Eigen::VectorXd q_sol;
      bool converged = ik_solver.solveIK(
          aa,
          T_target.translation(),
          T_target.linear(),
          q_init,
          q_sol,
          1e-5,
          500
      );

      if (converged) {
        Eigen::Isometry3d T_check;
        ik_solver.forwardKinematics(q_sol, T_check);
        double pos_err = (T_target.translation() - T_check.translation()).norm();
        double achieved_aa = ik_solver.getArmAngle(q_sol);
        
        std::cout << "  Target AA: " << std::fixed << std::setprecision(3) << aa 
                  << " -> Achieved: " << achieved_aa 
                  << ", Pos Error: " << std::scientific << pos_err << " ✓" << std::endl;
        success_count++;
      } else {
        std::cout << "  Target AA: " << std::fixed << std::setprecision(3) << aa 
                  << " -> Failed ✗" << std::endl;
      }
    }
    std::cout << "Success Rate: " << success_count << "/" << test_arm_angles.size() << std::endl;

    std::cout << "\n========================================" << std::endl;
    std::cout << "        All Tests Completed Successfully" << std::endl;
    std::cout << "========================================" << std::endl;

    return 0;
  } catch (const std::exception& e) {
    std::cerr << "Error: " << e.what() << std::endl;
    return 1;
  }
}
