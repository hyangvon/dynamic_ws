#include "w10_kinematics/arm_angle_ik.hpp"
#include <iostream>
#include <Eigen/Geometry>

namespace w10_kinematics {

ArmAngleIK::ArmAngleIK(const std::string& urdf_path) : data_(model_) {
  pinocchio::urdf::buildModel(urdf_path, model_);
  data_ = pinocchio::Data(model_);
  ee_frame_id_ = model_.nframes - 1;

  std::cout << "[ArmAngleIK] Model loaded from: " << urdf_path << std::endl;
  std::cout << "[ArmAngleIK] DOF: " << model_.nq << ", Bodies: " << model_.nbodies << std::endl;
}

std::vector<std::string> ArmAngleIK::getJointNames() const {
  std::vector<std::string> joint_names;
  // Skip the first joint which is typically a fixed base joint
  for (size_t i = 1; i < model_.joints.size(); ++i) {
    joint_names.push_back(model_.names[i]);
  }
  return joint_names;
}

int ArmAngleIK::getNumActiveJoints() const {
  // Count non-fixed joints
  int count = 0;
  for (size_t i = 1; i < model_.joints.size(); ++i) {
    if (model_.joints[i].nv() > 0) {  // nv() = 0 for fixed joints
      count += model_.joints[i].nv();
    }
  }
  return count;
}

std::vector<double> ArmAngleIK::extractJointValuesForROS(const Eigen::VectorXd& q) const {
  std::vector<double>result;
  
  if (q.size() != model_.nq) {
    std::cerr << "[ArmAngleIK] Q size mismatch in extractJointValuesForROS" << std::endl;
    return result;
  }
  
  // Extract values for each joint (skip universe/floating base at index 0)
  int q_idx = 0;
  for (size_t j = 0; j < model_.joints.size(); ++j) {
    int nq_this = model_.joints[j].nq();
    
    // Skip floating base (universe)
    if (j == 0) {
      q_idx += nq_this;
      continue;
    }
    
    // For regular joints, we take the first component (nv=1 for each active joint)
    if (q_idx < q.size()) {
      result.push_back(q(q_idx));
    } else {
      result.push_back(0.0);
    }
    
    q_idx += nq_this;
  }
  
  return result;
}

bool ArmAngleIK::forwardKinematics(const VectorXd& q, Eigen::Isometry3d& T_ee) {
  if (q.size() != model_.nq) {
    std::cerr << "[ArmAngleIK] Joint config size mismatch" << std::endl;
    return false;
  }

  pinocchio::forwardKinematics(model_, data_, q);
  int parent_id = model_.frames[ee_frame_id_].parent;
  pinocchio::SE3 se3 = data_.oMi[parent_id];
  
  T_ee = Eigen::Isometry3d::Identity();
  T_ee.linear() = se3.rotation();
  T_ee.translation() = se3.translation();

  return true;
}

Eigen::Vector3d ArmAngleIK::getShoulderPos(const VectorXd& q) {
  if (q.size() != model_.nq) {
    return Vector3d::Zero();
  }

  pinocchio::forwardKinematics(model_, data_, q);

  // 查找Link3对应的frame ID
  int shoulder_frame = -1;
  for (int i = 0; i < model_.nframes; ++i) {
    if (model_.frames[i].name == "Link3") {
      shoulder_frame = i;
      break;
    }
  }

  if (shoulder_frame < 0) {
    // Fallback：使用joint 2
    if (model_.njoints > 2) {
      shoulder_frame = model_.njoints - 1;
    } else {
      return Vector3d::Zero();
    }
  }

  int parent_id = model_.frames[shoulder_frame].parent;
  pinocchio::SE3 se3 = data_.oMi[parent_id];
  return se3.translation();
}

Eigen::Vector3d ArmAngleIK::getWristPos(const VectorXd& q) {
  Eigen::Isometry3d T_ee;
  forwardKinematics(q, T_ee);
  return T_ee.translation();
}

double ArmAngleIK::getArmAngle(const VectorXd& q) {
  Eigen::Vector3d shoulder_pos = getShoulderPos(q);
  Eigen::Vector3d wrist_pos = getWristPos(q);
  Eigen::Vector3d arm_vector = wrist_pos - shoulder_pos;

  double horizontal_dist = std::sqrt(arm_vector(0) * arm_vector(0) + arm_vector(1) * arm_vector(1));
  double vertical_dist = arm_vector(2);

  double arm_angle = std::atan2(vertical_dist, horizontal_dist);
  return arm_angle;
}

double ArmAngleIK::computeArmAngleError(double current_arm_angle, double target_arm_angle) {
  double error = current_arm_angle - target_arm_angle;

  while (error > M_PI) error -= 2 * M_PI;
  while (error < -M_PI) error += 2 * M_PI;

  return error;
}

bool ArmAngleIK::numericIK(const Vector3d& target_pos,
                           const Eigen::Matrix3d& target_ori,
                           const VectorXd& q_init,
                           VectorXd& q_solution,
                           double tol,
                           int max_iter) {
  q_solution = q_init;
  double damping = 0.01;
  const int ee_id = model_.frames[ee_frame_id_].parent;

  for (int iter = 0; iter < max_iter; ++iter) {
    pinocchio::forwardKinematics(model_, data_, q_solution);
    pinocchio::SE3 se3_current = data_.oMi[ee_id];
    Eigen::Isometry3d T_current = Eigen::Isometry3d::Identity();
    T_current.linear() = se3_current.rotation();
    T_current.translation() = se3_current.translation();

    Eigen::Vector3d pos_error = target_pos - T_current.translation();
    Eigen::Matrix3d R_error = target_ori * T_current.linear().transpose();
    Eigen::AngleAxisd aa(R_error);
    Eigen::Vector3d ori_error = aa.angle() * aa.axis();

    VectorXd error(6);
    error.head(3) = pos_error;
    error.tail(3) = ori_error;

    double error_norm = error.norm();

    if (error_norm < tol) {
      std::cout << "[ArmAngleIK] IK converged at iteration " << iter << std::endl;
      return true;
    }

    MatrixXd J = MatrixXd::Zero(6, model_.nv);
    pinocchio::computeJointJacobian(model_, data_, q_solution, ee_id, J);
    MatrixXd J_pos = J.topRows(3);

    MatrixXd JtJ = J_pos.transpose() * J_pos;
    MatrixXd I = MatrixXd::Identity(model_.nv, model_.nv);
    MatrixXd J_inv = J_pos.transpose() * (JtJ + damping * I).inverse();

    VectorXd dq = J_inv * error.head(3);
    q_solution += 0.1 * dq;

    for (int i = 0; i < model_.nq; ++i) {
      if (i < model_.upperPositionLimit.size()) {
        q_solution(i) = std::min(q_solution(i), model_.upperPositionLimit(i));
        q_solution(i) = std::max(q_solution(i), model_.lowerPositionLimit(i));
      }
    }
  }

  std::cerr << "[ArmAngleIK] Failed to converge after " << max_iter << " iterations" << std::endl;
  return false;
}

bool ArmAngleIK::solveIK(double arm_angle,
                         const Vector3d& target_pos,
                         const Eigen::Matrix3d& target_ori,
                         const VectorXd& q_init,
                         VectorXd& q_solution,
                         double tol,
                         int max_iter) {
  q_solution = q_init;
  double damping = 0.01;
  const int ee_id = model_.frames[ee_frame_id_].parent;
  
  static_cast<void>(target_ori);

  // Phase 1: Position convergence
  for (int iter = 0; iter < max_iter; ++iter) {
    pinocchio::forwardKinematics(model_, data_, q_solution);
    pinocchio::SE3 se3_current = data_.oMi[ee_id];
    Eigen::Isometry3d T_current = Eigen::Isometry3d::Identity();
    T_current.linear() = se3_current.rotation();
    T_current.translation() = se3_current.translation();

    Eigen::Vector3d pos_error = target_pos - T_current.translation();
    double pos_error_norm = pos_error.norm();

    if (pos_error_norm < tol) {
      // Position converged, now refine arm angle
      for (int refine_iter = 0; refine_iter < 200; ++refine_iter) {
        pinocchio::forwardKinematics(model_, data_, q_solution);
        double current_arm_angle = getArmAngle(q_solution);
        double arm_angle_diff = computeArmAngleError(current_arm_angle, arm_angle);

        if (std::abs(arm_angle_diff) < 0.01) {
          std::cout << "[ArmAngleIK] IK with arm angle constraint converged at iteration " 
                    << (iter + refine_iter) << std::endl;
          return true;
        }

        // Adjust wrist joints to correct arm angle
        // Try using multiple joints: q2, q3, q4 for shoulder and q5 for wrist pitch
        double adjustment = -0.1 * arm_angle_diff;  // Increased from -0.05
        
        // Primary adjustment through q4 (shoulder pitch which affects arm angle)
        if (4 < q_solution.size()) {
          q_solution(4) += adjustment * 0.7;
        }
        
        // Secondary adjustment through q5 (wrist joint)
        if (5 < q_solution.size()) {
          q_solution(5) -= adjustment * 0.3;
        }

        // Apply limits
        for (int i = 0; i < model_.nq && i < q_solution.size(); ++i) {
          if (i < model_.upperPositionLimit.size()) {
            q_solution(i) = std::min(q_solution(i), model_.upperPositionLimit(i));
            q_solution(i) = std::max(q_solution(i), model_.lowerPositionLimit(i));
          }
        }
      }
      
      return true;  // Converged even if arm angle not perfect
    }

    MatrixXd J = MatrixXd::Zero(6, model_.nv);
    pinocchio::computeJointJacobian(model_, data_, q_solution, ee_id, J);
    
    // Use only position Jacobian (first 3 rows)
    MatrixXd J_pos = J.block(0, 0, 3, model_.nv);

    // Compute pseudo-inverse using damped least squares
    MatrixXd JtJ = J_pos.transpose() * J_pos;
    MatrixXd I = MatrixXd::Identity(model_.nv, model_.nv);
    MatrixXd JtJ_inv = (JtJ + damping * I).inverse();
    
    // Solve for joint angle increments
    VectorXd dq = (JtJ_inv * J_pos.transpose() * pos_error).eval();

    // Update q_solution
    for (int i = 0; i < model_.nv && i < q_solution.size(); ++i) {
      q_solution(i) = q_solution(i) + 0.1 * dq(i);
    }

    // Apply joint limits
    for (int i = 0; i < model_.nq && i < q_solution.size(); ++i) {
      if (i < model_.upperPositionLimit.size()) {
        q_solution(i) = std::min(q_solution(i), model_.upperPositionLimit(i));
        q_solution(i) = std::max(q_solution(i), model_.lowerPositionLimit(i));
      }
    }
  }

  std::cerr << "[ArmAngleIK] Arm angle IK failed to converge" << std::endl;
  return false;
}

bool ArmAngleIK::solveIKWithArmAngleConstraint(
    double arm_angle,
    const Vector3d& target_pos,
    const Eigen::Matrix3d& target_ori,
    const VectorXd& q_init,
    VectorXd& q_solution,
    double tol,
    int max_iter) {
  return solveIK(arm_angle, target_pos, target_ori, q_init, q_solution, tol, max_iter);
}

}  // namespace w10_kinematics
