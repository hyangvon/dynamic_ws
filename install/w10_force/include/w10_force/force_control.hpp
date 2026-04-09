#ifndef W10_FORCE_FORCE_CONTROL_HPP_
#define W10_FORCE_FORCE_CONTROL_HPP_

#include <Eigen/Dense>
#include <vector>

namespace w10_force {

class ForceController {
public:
  ForceController();
  ~ForceController() = default;

  // Initialize the force controller
  void initialize();

  // Calculate force control command
  Eigen::VectorXd compute_control(const Eigen::VectorXd& force);

private:
  Eigen::MatrixXd gain_matrix_;
  double control_frequency_;
};

}  // namespace w10_force

#endif  // W10_FORCE_FORCE_CONTROL_HPP_
