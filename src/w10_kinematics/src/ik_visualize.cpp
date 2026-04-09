#include "w10_kinematics/arm_angle_ik.hpp"
#include <rclcpp/rclcpp.hpp>
#include <sensor_msgs/msg/joint_state.hpp>
#include <iostream>
#include <chrono>
#include <iomanip>

using namespace std::chrono_literals;

class IKVisualizer : public rclcpp::Node {
public:
  IKVisualizer() : Node("ik_visualizer") {
    std::string urdf_path = "/home/user/ros2_ws/dynamic_ws/install/w10_sim/share/w10_sim/urdf/w10.urdf";
    ik_solver_ = std::make_unique<w10_kinematics::ArmAngleIK>(urdf_path);
    ndof_ = ik_solver_->getNDOF();

    // Create publisher
    joint_state_pub_ = this->create_publisher<sensor_msgs::msg::JointState>(
        "joint_states", 10);

    // Create timer for publishing
    timer_ = this->create_wall_timer(
        500ms, std::bind(&IKVisualizer::timerCallback, this));

    RCLCPP_INFO(this->get_logger(), "IK Visualizer initialized with %d DOF", ndof_);
    
    // Initialize joint names from the loaded model
    joint_names_ = ik_solver_->getJointNames();
    
    RCLCPP_INFO(this->get_logger(), "Joint names (%zu joints): ", joint_names_.size());
    for (size_t i = 0; i < joint_names_.size(); ++i) {
      RCLCPP_INFO(this->get_logger(), "  [%zu] %s", i, joint_names_[i].c_str());
    }

    current_state_ = 0;
  }

private:
  void timerCallback() {
    auto msg = sensor_msgs::msg::JointState();
    msg.header.stamp = this->now();
    msg.name = joint_names_;
    int num_joints = joint_names_.size();
    msg.position.resize(num_joints);
    msg.velocity.resize(num_joints, 0.0);
    msg.effort.resize(num_joints, 0.0);

    // Generate different IK solutions cyclically
    switch (current_state_) {
      case 0: {
        RCLCPP_INFO(this->get_logger(), "\n=== STATE 0: IK Solving from Perturbed Config ===");
        
        Eigen::VectorXd q_init = Eigen::VectorXd::Zero(ndof_);
        q_init(4) = 0.5;
        q_init(5) = 0.3;
        q_init(6) = -0.8;
        
        Eigen::VectorXd q_solution;
        Eigen::Vector3d target_pos(0.0, 0.0, 0.7698);
        Eigen::Matrix3d target_ori = Eigen::Matrix3d::Identity();
        double target_arm_angle = 0.5;
        
        RCLCPP_INFO(this->get_logger(), "Initial Config: q2=0.5, q3=0.3, q4=-0.8");
        RCLCPP_INFO(this->get_logger(), "Target Position: [%.4f, %.4f, %.4f]",
            target_pos(0), target_pos(1), target_pos(2));
        RCLCPP_INFO(this->get_logger(), "Solving IK...");
        
        bool success = ik_solver_->solveIK(
            target_arm_angle, target_pos, target_ori, q_init, q_solution, 1e-5, 1000);
        
        if (success) {
          RCLCPP_INFO(this->get_logger(), "✓ IK CONVERGED");
          publishJointState(q_solution, msg);
          
          Eigen::Isometry3d T_verify;
          if (ik_solver_->forwardKinematics(q_solution, T_verify)) {
            Eigen::Vector3d pos_error = target_pos - T_verify.translation();
            double error_norm = pos_error.norm();
            
            RCLCPP_INFO(this->get_logger(), "Verification (FK):");
            RCLCPP_INFO(this->get_logger(), "  Achieved Position: [%.4f, %.4f, %.4f]",
                T_verify.translation()(0), T_verify.translation()(1), T_verify.translation()(2));
            RCLCPP_INFO(this->get_logger(), "  Position Error: %.2e m", error_norm);
          }
        } else {
          RCLCPP_WARN(this->get_logger(), "✗ IK FAILED");
          Eigen::VectorXd q_zero = Eigen::VectorXd::Zero(ndof_);
          publishJointState(q_zero, msg);
        }
        break;
      }
      
      case 1: {
        RCLCPP_INFO(this->get_logger(), "\n=== STATE 1: IK Solving from Different Initial Config ===");
        
        Eigen::VectorXd q_init = Eigen::VectorXd::Zero(ndof_);
        q_init(4) = -0.4;
        q_init(5) = -0.2;
        q_init(6) = 0.6;
        
        Eigen::VectorXd q_solution;
        Eigen::Vector3d target_pos(0.0, 0.0, 0.7698);
        Eigen::Matrix3d target_ori = Eigen::Matrix3d::Identity();
        double target_arm_angle = 0.3;
        
        RCLCPP_INFO(this->get_logger(), "Initial Config: q2=-0.4, q3=-0.2, q4=0.6");
        RCLCPP_INFO(this->get_logger(), "Target Position: [%.4f, %.4f, %.4f]",
            target_pos(0), target_pos(1), target_pos(2));
        RCLCPP_INFO(this->get_logger(), "Solving IK...");
        
        bool success = ik_solver_->solveIK(
            target_arm_angle, target_pos, target_ori, q_init, q_solution, 1e-5, 1000);
        
         if (success) {
          RCLCPP_INFO(this->get_logger(), "✓ IK CONVERGED");
          publishJointState(q_solution, msg);
          
          Eigen::Isometry3d T_verify;
          if (ik_solver_->forwardKinematics(q_solution, T_verify)) {
            Eigen::Vector3d pos_error = target_pos - T_verify.translation();
            double error_norm = pos_error.norm();
            
            RCLCPP_INFO(this->get_logger(), "Verification (FK):");
            RCLCPP_INFO(this->get_logger(), "  Achieved Position: [%.4f, %.4f, %.4f]",
                T_verify.translation()(0), T_verify.translation()(1), T_verify.translation()(2));
            RCLCPP_INFO(this->get_logger(), "  Position Error: %.2e m", error_norm);
          }
        } else {
          RCLCPP_WARN(this->get_logger(), "✗ IK FAILED");
          Eigen::VectorXd q_zero = Eigen::VectorXd::Zero(ndof_);
          publishJointState(q_zero, msg);
        }
        break;
      }
      
      case 2: {
        RCLCPP_INFO(this->get_logger(), "\n=== STATE 2: IK Solving from Large Perturbation ===");
        
        Eigen::VectorXd q_init = Eigen::VectorXd::Zero(ndof_);
        q_init(4) = -0.7;
        q_init(5) = 0.5;
        q_init(6) = -1.0;
        q_init(7) = 0.8;
        
        Eigen::VectorXd q_solution;
        Eigen::Vector3d target_pos(0.0, 0.0, 0.7698);
        Eigen::Matrix3d target_ori = Eigen::Matrix3d::Identity();
        double target_arm_angle = 0.0;
        
        RCLCPP_INFO(this->get_logger(), "Initial Config: q2=-0.7, q3=0.5, q4=-1.0, q5=0.8");
        RCLCPP_INFO(this->get_logger(), "Target Position: [%.4f, %.4f, %.4f]",
            target_pos(0), target_pos(1), target_pos(2));
        RCLCPP_INFO(this->get_logger(), "Solving IK...");
        
        bool success = ik_solver_->solveIK(
            target_arm_angle, target_pos, target_ori, q_init, q_solution, 1e-5, 1000);
        
        if (success) {
          RCLCPP_INFO(this->get_logger(), "✓ IK CONVERGED");
          publishJointState(q_solution, msg);
          
          Eigen::Isometry3d T_verify;
          if (ik_solver_->forwardKinematics(q_solution, T_verify)) {
            Eigen::Vector3d pos_error = target_pos - T_verify.translation();
            double error_norm = pos_error.norm();
            
            RCLCPP_INFO(this->get_logger(), "Verification (FK):");
            RCLCPP_INFO(this->get_logger(), "  Achieved Position: [%.4f, %.4f, %.4f]",
                T_verify.translation()(0), T_verify.translation()(1), T_verify.translation()(2));
            RCLCPP_INFO(this->get_logger(), "  Position Error: %.2e m", error_norm);
          }
        } else {
          RCLCPP_WARN(this->get_logger(), "✗ IK FAILED");
          Eigen::VectorXd q_zero = Eigen::VectorXd::Zero(ndof_);
          publishJointState(q_zero, msg);
        }
        break;
      }
      
      case 3: {
        RCLCPP_INFO(this->get_logger(), "\n=== STATE 3: Zero Configuration ===");
        
        Eigen::VectorXd q_zero = Eigen::VectorXd::Zero(ndof_);
        publishJointState(q_zero, msg);
        break;
      }
    }
    
    joint_state_pub_->publish(msg);
    
    // Cycle through states
    current_state_ = (current_state_ + 1) % 4;
  }
  
  void publishJointState(const Eigen::VectorXd& q_solution, sensor_msgs::msg::JointState& msg) {
    // Extract joint values using the correct mapping  from Pinocchio q to ROS joint_state
    std::vector<double> joint_values = ik_solver_->extractJointValuesForROS(q_solution);
    
    int num_joints = joint_names_.size();
    for (int i = 0; i < num_joints && i < (int)joint_values.size(); ++i) {
      msg.position[i] = joint_values[i];
    }
  }

  rclcpp::Publisher<sensor_msgs::msg::JointState>::SharedPtr joint_state_pub_;
  rclcpp::TimerBase::SharedPtr timer_;
  std::unique_ptr<w10_kinematics::ArmAngleIK> ik_solver_;
  int ndof_;
  int current_state_;
  std::vector<std::string> joint_names_;
};

int main(int argc, char* argv[]) {
  rclcpp::init(argc, argv);
  auto node = std::make_shared<IKVisualizer>();
  rclcpp::spin(node);
  rclcpp::shutdown();
  return 0;
}
