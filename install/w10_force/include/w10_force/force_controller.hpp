#ifndef W10_FORCE__FORCE_CONTROLLER_HPP_
#define W10_FORCE__FORCE_CONTROLLER_HPP_

#include <Eigen/Dense>
#include <memory>
#include "pinocchio/multibody/model.hpp"
#include "pinocchio/multibody/data.hpp"

namespace w10_force {

class ForceController {
 public:
  ForceController();
  ~ForceController() = default;

  // Initialize force controller with robot model
  void initialize(const std::string& urdf_path);

  // Compute force control commands
  Eigen::VectorXd computeForceTorque(
      const Eigen::VectorXd& desired_force,
      const Eigen::Vector3d& contact_position);

  // Set desired end-effector force
  void setDesiredForce(const Eigen::Vector3d& force);

  // Get current computed torque
  Eigen::VectorXd getTorques() const;

 private:
  std::unique_ptr<pinocchio::Model> model_;
  std::unique_ptr<pinocchio::Data> data_;
  Eigen::Vector3d desired_force_;
  Eigen::VectorXd computed_torques_;
};

}  // namespace w10_force

#endif  // W10_FORCE__FORCE_CONTROLLER_HPP_
