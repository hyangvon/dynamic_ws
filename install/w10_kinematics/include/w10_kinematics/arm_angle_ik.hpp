#ifndef W10_KINEMATICS_ARM_ANGLE_IK_HPP_
#define W10_KINEMATICS_ARM_ANGLE_IK_HPP_

#include <Eigen/Dense>
#include <pinocchio/fwd.hpp>
#include <pinocchio/algorithm/kinematics.hpp>
#include <pinocchio/algorithm/jacobian.hpp>
#include <pinocchio/multibody/model.hpp>
#include <pinocchio/multibody/data.hpp>
#include <pinocchio/parsers/urdf.hpp>
#include <vector>
#include <cmath>

namespace w10_kinematics {

class ArmAngleIK {
public:
  using VectorXd = Eigen::VectorXd;
  using MatrixXd = Eigen::MatrixXd;
  using Vector3d = Eigen::Vector3d;

  // 构造函数
  ArmAngleIK(const std::string& urdf_path);
  ~ArmAngleIK() = default;

  // 获取机器臂基本信息
  int getNDOF() const { return model_.nq; }
  int getNBodies() const { return model_.nbodies; }
  std::vector<std::string> getJointNames() const;
  int getNumActiveJoints() const;
  
  // Extract joint values from q vector by joint index
  std::vector<double> extractJointValuesForROS(const Eigen::VectorXd& q) const;

  // 正向运动学
  bool forwardKinematics(const VectorXd& q, Eigen::Isometry3d& T_ee);

  // 获取臂角（肩部到腕部连线与水平面的夹角）
  double getArmAngle(const VectorXd& q);

  // 基于臂角降维的逆运动学求解
  // arm_angle: 约束的臂角（弧度）
  // target_pos: 目标末端位置
  // target_ori: 目标末端姿态
  // q_init: 初始配置
  // q_solution: 求解结果
  bool solveIK(double arm_angle,
               const Vector3d& target_pos,
               const Eigen::Matrix3d& target_ori,
               const VectorXd& q_init,
               VectorXd& q_solution,
               double tol = 1e-6,
               int max_iter = 1000);

  // 基于臂角的逆运动学（带约束优化）
  bool solveIKWithArmAngleConstraint(
      double arm_angle,
      const Vector3d& target_pos,
      const Eigen::Matrix3d& target_ori,
      const VectorXd& q_init,
      VectorXd& q_solution,
      double tol = 1e-6,
      int max_iter = 1000);

  // 获取机器臂模型和数据
  const pinocchio::Model& getModel() const { return model_; }
  pinocchio::Data& getData() { return data_; }

private:
  pinocchio::Model model_;
  pinocchio::Data data_;
  int ee_frame_id_;

  // 计算肩部（joint3）位置
  Vector3d getShoulderPos(const VectorXd& q);

  // 计算腕部（末端执行器）位置的初步估计
  Vector3d getWristPos(const VectorXd& q);

  // 计算臂角约束条件
  double computeArmAngleError(double current_arm_angle, double target_arm_angle);

  // 数值IK求解
  bool numericIK(const Vector3d& target_pos,
                 const Eigen::Matrix3d& target_ori,
                 const VectorXd& q_init,
                 VectorXd& q_solution,
                 double tol,
                 int max_iter);
};

}  // namespace w10_kinematics

#endif  // W10_KINEMATICS_ARM_ANGLE_IK_HPP_
