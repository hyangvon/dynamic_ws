#include <cppad/cppad.hpp>
#include <cppad/example/cppad_eigen.hpp>

#include <pinocchio/parsers/urdf.hpp>
#include <pinocchio/algorithm/crba.hpp>
#include <pinocchio/algorithm/kinematics.hpp>
#include <pinocchio/algorithm/aba.hpp>
#include <pinocchio/algorithm/energy.hpp>
#include <pinocchio/algorithm/frames.hpp>
#include <pinocchio/algorithm/jacobian.hpp>
#include <pinocchio/algorithm/centroidal.hpp>
#include <pinocchio/multibody/model.hpp>
#include <pinocchio/multibody/data.hpp>

#include <Eigen/Dense>

#include <rclcpp/rclcpp.hpp>

#include <iostream>
#include <fstream>
#include <vector>
#include <chrono>
#include <numeric>
#include <string>
#include <sstream>
#include <algorithm>
#include <iomanip>

// Fix Eigen <-> CppAD compatibility for isfinite()
namespace Eigen {
    namespace numext {
        template<>
        EIGEN_STRONG_INLINE bool isfinite(const CppAD::AD<double>&) {
            return true;
        }
    }
}

using namespace pinocchio;
using namespace std::chrono;

// ---------- type aliases ----------
using ADScalar = CppAD::AD<double>;
using VecAD = Eigen::Matrix<ADScalar, Eigen::Dynamic, 1>;
using MatAD = Eigen::Matrix<ADScalar, Eigen::Dynamic, Eigen::Dynamic>;
using Vec  = Eigen::VectorXd;
using Mat  = Eigen::MatrixXd;
using ModelAD = pinocchio::ModelTpl<ADScalar>;
using DataAD  = pinocchio::DataTpl<ADScalar>;

// 计算末端位姿（位置 + 旋转矩阵）
std::pair<Eigen::Vector3d, Eigen::Matrix3d>
compute_end_effector_pose(const Model &model,
                          Data &data,
                          int frame_id,
                          const Vec &q)
{
    pinocchio::forwardKinematics(model, data, q);
    pinocchio::updateFramePlacements(model, data);

    Eigen::Vector3d ee_pos = data.oMf[frame_id].translation();
    Eigen::Matrix3d ee_rot = data.oMf[frame_id].rotation();

    return {ee_pos, ee_rot};
}

// 计算末端 frame 上 Cartesian 力映射到广义力 (世界坐标对齐)
Vec compute_ext_generalized_force(const Model &model, Data &data,
                                   pinocchio::FrameIndex frame_id, const Vec &q,
                                   const Eigen::Vector3d &cartesian_force)
{
    Mat J_full = Mat::Zero(6, model.nv);
    pinocchio::computeFrameJacobian(model, data, q, frame_id,
                                    pinocchio::LOCAL_WORLD_ALIGNED, J_full);
    return J_full.topRows(3).transpose() * cartesian_force;
}

// ---------- double helpers (non-AD) ----------
Mat inertia_matrix(const Model &model, Data &data, const Vec &q)
{
    pinocchio::crba(model, data, q);
    return data.M;
}

double kinetic_energy(const Model &model, Data &data, const Vec &q_mid, const Vec &qdot)
{
    pinocchio::crba(model, data, q_mid);
    Mat M = data.M;
    return 0.5 * qdot.transpose() * M * qdot;
}

double potential_energy(const Model &model, Data &data, const Vec &q)
{
    return pinocchio::computePotentialEnergy(model, data, q);
}

// double discrete Lagrangian (used for Ed numeric)
double discrete_lagrangian_double(const Model &model, Data &data, const Vec &q0, const Vec &q1, double h)
{
    const Vec q_mid = 0.5 * (q0 + q1);
    const Vec dq = (q1 - q0) / h;
    const double T = kinetic_energy(model, data, q_mid, dq);
    const double U = potential_energy(model, data, q_mid);
    return h * (T - U);
}

double compute_energy(const Model &model, Data &data, const Vec &q0, const Vec &q1, const double h)
{
    const Vec q_mid = 0.5 * (q0 + q1);
    const Vec dq = (q1 - q0) / h;
    const double T = kinetic_energy(model, data, q_mid, dq);
    const double U = potential_energy(model, data, q_mid);
    return T + U;
}

// numeric discrete energy Ed = -dL/dh (centered difference)
double discrete_energy_numeric(const Model &model, Data &data, const Vec &q0, const Vec &q1, double h, double eps_h = 1e-8)
{
    double Lp = discrete_lagrangian_double(model, data, q0, q1, h + eps_h);
    double Lm = discrete_lagrangian_double(model, data, q0, q1, h - eps_h);
    double dLdh = (Lp - Lm) / (2.0 * eps_h);
    return -dLdh;
}

// 计算能量对步长的梯度 dE/dh (Lyapunov 核心)
double compute_energy_gradient(const ModelAD &model_ad, DataAD &data_ad, const Vec &q0, const Vec &q1, double h) {
    CppAD::vector<ADScalar> h_ad(1);
    h_ad[0] = h;
    CppAD::Independent(h_ad);

    VecAD q0_ad = q0.cast<ADScalar>();
    VecAD q1_ad = q1.cast<ADScalar>();
    VecAD q_mid = (q0_ad + q1_ad) * ADScalar(0.5);
    VecAD dq = (q1_ad - q0_ad) / h_ad[0];

    pinocchio::crba(model_ad, data_ad, q_mid);
    data_ad.M.template triangularView<Eigen::Upper>() = data_ad.M.transpose().template triangularView<Eigen::Upper>();

    ADScalar T = ADScalar(0.5) * dq.dot(data_ad.M * dq);
    ADScalar U = pinocchio::computePotentialEnergy(model_ad, data_ad, q_mid);

    CppAD::vector<ADScalar> y(1);
    y[0] = T + U;

    CppAD::ADFun<double> f(h_ad, y);
    CppAD::vector<double> h_val(1); h_val[0] = h;
    return f.Jacobian(h_val)[0];
}

// ---------- AD discrete Lagrangian ----------
ADScalar discreteLagrangian_ad(const ModelAD &model_ad, DataAD &data_ad,
                               const VecAD &q0_ad, const VecAD &q1_ad, double h)
{
    VecAD q_mid = ADScalar(0.5) * (q0_ad + q1_ad);
    VecAD dq = (q1_ad - q0_ad) / ADScalar(h);

    pinocchio::crba(model_ad, data_ad, q_mid); // fills data_ad.M (AD)
    MatAD M = data_ad.M;

    ADScalar T = ADScalar(0.5) * dq.transpose() * (M * dq);
    ADScalar U = pinocchio::computePotentialEnergy(model_ad, data_ad, q_mid);

    return ADScalar(h) * (T - U);
}

// ---------- AD gradients D1, D2 (returns double vector evaluated at q) ----------
Vec D_1(const ModelAD &model_ad, DataAD &data_ad, const Vec &q0, const Vec &q1, double h)
{
    const int n = q0.size();
    // independent variables: q0
    CppAD::vector<ADScalar> x_ad(n);
    for (int i=0;i<n;++i) x_ad[i] = q0[i];
    CppAD::Independent(x_ad);

    VecAD q0_ad = Eigen::Map<VecAD>(x_ad.data(), n);
    VecAD q1_ad = q1.cast<ADScalar>();

    ADScalar Ld = discreteLagrangian_ad(model_ad, data_ad, q0_ad, q1_ad, h);
    CppAD::vector<ADScalar> y(1);
    y[0] = Ld;

    CppAD::ADFun<double> f;
    f.Dependent(x_ad, y);

    CppAD::vector<double> x0(n);
    for (int i=0;i<n;++i) x0[i] = q0[i];

    CppAD::vector<double> jac = f.Jacobian(x0); // y dim 1 -> gradient length n

    Vec grad(n);
    for (int i=0;i<n;++i) grad[i] = jac[i];
    return grad;
}

Vec D_2(const ModelAD &model_ad, DataAD &data_ad, const Vec &q0, const Vec &q1, double h)
{
    const int n = q1.size();
    // independent variables: q1
    CppAD::vector<ADScalar> x_ad(n);
    for (int i=0;i<n;++i) x_ad[i] = q1[i];
    CppAD::Independent(x_ad);

    VecAD q0_ad = q0.cast<ADScalar>();
    VecAD q1_ad = Eigen::Map<VecAD>(x_ad.data(), n);

    ADScalar Ld = discreteLagrangian_ad(model_ad, data_ad, q0_ad, q1_ad, h);
    CppAD::vector<ADScalar> y(1);
    y[0] = Ld;

    CppAD::ADFun<double> f;
    f.Dependent(x_ad, y);

    CppAD::vector<double> x0(n);
    for (int i=0;i<n;++i) x0[i] = q1[i];

    CppAD::vector<double> jac = f.Jacobian(x0);

    Vec grad(n);
    for (int i=0;i<n;++i) grad[i] = jac[i];
    return grad;
}

struct SolverInfo { bool converged; std::string reason; int iterations; double residual_norm; };

// VI_init: 正确的初始步求解器
// 残差: M(q0)*v0 + D1(q0, q1, h) - h*tau = 0
std::pair<Vec, SolverInfo> VI_init(const Model &model, Data &data,
                                   const ModelAD &model_ad, DataAD &data_ad,
                                   const Vec &q0, const Vec &v0,
                                   const Vec &tau_k, double h,
                                   double eps=1e-6, int max_iters=50, double tol=1e-8)
{
    int n = q0.size();
    Vec q1 = q0 + h * v0;  // initial guess
    SolverInfo info{false, "", 0, 0.0};
    for (int it = 0; it < max_iters; ++it)
    {
        Mat M = inertia_matrix(model, data, q0);
        Vec D1 = D_1(model_ad, data_ad, q0, q1, h);
        Vec R = M * v0 + D1 - h * tau_k;
        double normR = R.norm();
        info.iterations = it;
        info.residual_norm = normR;
        if (normR < tol) { info.converged = true; return {q1, info}; }
        Mat J = Mat::Zero(n, n);
        for (int j = 0; j < n; ++j)
        {
            Vec dq = Vec::Zero(n); dq(j) = eps;
            Vec D1p = D_1(model_ad, data_ad, q0, q1 + dq, h);
            Vec D1m = D_1(model_ad, data_ad, q0, q1 - dq, h);
            J.col(j) = (D1p - D1m) / (2.0 * eps);
        }
        Mat A = J + 1e-9 * Mat::Identity(n, n);
        Eigen::ColPivHouseholderQR<Mat> ls(A);
        if (ls.rank() < n) { info.converged = false; info.reason = "singular_jacobian"; return {q1, info}; }
        q1 += ls.solve(-R);
    }
    info.converged = false; info.reason = "max_iters";
    return {q1, info};
}

// 变步长 DEL 求解器: h_prev 用于 D2, h_curr 用于 D1
// 残差: D2(q_prev, q_curr, h_prev) + D1(q_curr, q_next, h_curr) - h_curr * tau = 0
std::pair<Vec, SolverInfo> solve_q_next(const ModelAD &model_ad,
                                        DataAD &data_ad,
                                        const Vec &q_prev,
                                        const Vec &q_curr,
                                        const Vec &tau_k,
                                        double h_prev,    // q_prev→q_curr 区间的步长
                                        double h_curr,    // q_curr→q_next 区间的步长（本步）
                                        int max_iters=50,
                                        double tol=1e-8)
{
    int n = q_curr.size();
    Vec q_next = q_curr;
    SolverInfo info{false, "", 0, 0.0};

    for (int it = 0; it < max_iters; ++it)
    {
        // Vec D2 = D_2(model_ad, data_ad, q_prev, q_curr, h_prev);  // 用上一步的 h
        Vec D2 = D_2(model_ad, data_ad, q_prev, q_curr, h_curr);  // 用本步的 h
        Vec D1 = D_1(model_ad, data_ad, q_curr, q_next, h_curr);  // 用本步的 h
        Vec R = D2 + D1 - h_curr * tau_k;
        double normR = R.norm();
        info.iterations = it;
        info.residual_norm = normR;
        if (normR < tol) { info.converged = true; return {q_next, info}; }

        // D1 关于 q_next 的数值 Jacobian（D2 固定，与 q_next 无关）
        Mat J = Mat::Zero(n, n);
        double eps = 1e-6;
        for (int j = 0; j < n; ++j)
        {
            Vec dq = Vec::Zero(n);
            dq(j) = eps;
            Vec D1p = D_1(model_ad, data_ad, q_curr, q_next + dq, h_curr);
            Vec D1m = D_1(model_ad, data_ad, q_curr, q_next - dq, h_curr);
            J.col(j) = (D1p - D1m) / (2.0 * eps);
        }

        Mat A = J + 1e-9 * Mat::Identity(n, n);
        Eigen::ColPivHouseholderQR<Mat> solver(A);
        if (solver.rank() < n)
        {
            info.converged = false;
            info.reason = "singular_jacobian";
            return {q_next, info};
        }
        Vec delta = solver.solve(-R);
        q_next += delta;
    }

    info.converged = false;
    info.reason = "max_iters";
    return {q_next, info};
}

// CSV writers
void write_csv(const std::string &filename, const std::vector<Vec> &rows)
{
    if (rows.empty()) return;
    std::ofstream ofs(filename);
    int ncols = rows[0].size();
    for (size_t r=0;r<rows.size();++r)
    {
        for (int c=0;c<ncols;++c)
        {
            ofs << std::setprecision(15) << rows[r](c);
            if (c+1 < ncols) ofs << ",";
        }
        ofs << "\n";
    }
}

void write_csv_scalar_series(const std::string &filename, const std::vector<double> &rows)
{
    std::ofstream ofs(filename);
    for (double v : rows) ofs << std::setprecision(15) << v << "\n";
}

void write_csv_3d(const std::string &filename,
                  const std::vector<Eigen::Vector3d> &rows)
{
    std::ofstream ofs(filename);
    for (const auto &v : rows)
    {
        ofs << std::setprecision(15)
            << v(0) << "," << v(1) << "," << v(2) << "\n";
    }
}

void print_progress(double t_cur, double duration, std::vector<double> runtimes, double h_next) {
    int bar_width = 50;
    double progress = t_cur / duration;
    if (progress > 1.0) progress = 1.0;
    int pos = int(bar_width * progress);
    double avg_time = !runtimes.empty() ? std::accumulate(runtimes.begin(), runtimes.end(), 0.0) / runtimes.size() : 0.0;
    double time_left = avg_time * (duration - t_cur) / h_next;
    std::cout << "\r[";
    for (int i = 0; i < bar_width; ++i) {
        if (i < pos) std::cout << "=";
        else if (i == pos) std::cout << ">";
        else std::cout << " ";
    }
    std::cout << "] " << int(progress * 100.0) << "%, approx " << int(time_left/60) << "mins " << int(time_left) % 60 << "s left... ";
    std::cout.flush();
}

std::string expand_user(const std::string &path)
{
    if (!path.empty() && path[0] == '~') {
        const char* home = std::getenv("HOME");
        if (home) {
            return std::string(home) + path.substr(1);
        }
    }
    return path;
}

std::string fmt_double_label(double v)
{
    std::ostringstream oss;
    oss.setf(std::ios::fmtflags(0), std::ios::floatfield);
    oss<<std::fixed<<std::setprecision(6)<<v;
    std::string s = oss.str();
    if (s.find('.') != std::string::npos) {
        while (!s.empty() && s.back() == '0') s.pop_back();
        if (!s.empty() && s.back() == '.') s.pop_back();
    }
    std::replace(s.begin(), s.end(), '.', 'p');
    return s;
}

// ---------- Main ----------
int main(int argc, char** argv)
{
    std::cout.setf(std::ios::unitbuf);
    rclcpp::init(argc, argv);
    auto node = std::make_shared<rclcpp::Node>(
        "c_atsvi_node",
        rclcpp::NodeOptions().automatically_declare_parameters_from_overrides(true)
    );

    // Parameters (provide defaults via launch)
    std::vector<double> q_init_vec = node->get_parameter("q_init").as_double_array();
    double timestep = node->get_parameter("timestep").as_double();
    double duration = node->get_parameter("duration").as_double();
    double eps_diff = node->get_parameter("eps_diff").as_double();
    std::string urdf_path = expand_user(node->get_parameter("urdf_path").as_string());
    // Lyapunov 控制增益
    double alpha = node->get_parameter("lyap_alpha").as_double();
    double beta  = node->get_parameter("lyap_beta").as_double();

    RCLCPP_INFO(node->get_logger(), "Using URDF: %s", urdf_path.c_str());
    RCLCPP_INFO(node->get_logger(), "Duration = %.3f, Timestep(init) = %.6f, eps_diff = %.1e", duration, timestep, eps_diff);

    // ---------- 外力冲击激励参数 ----------
    auto declare_if_needed = [&](const std::string &name, rclcpp::ParameterValue default_val) {
        if (!node->has_parameter(name))
            node->declare_parameter(name, default_val);
    };
    declare_if_needed("force_enable",     rclcpp::ParameterValue(false));
    declare_if_needed("force_magnitude",  rclcpp::ParameterValue(50.0));
    declare_if_needed("force_dir_x",      rclcpp::ParameterValue(1.0));
    declare_if_needed("force_dir_y",      rclcpp::ParameterValue(0.0));
    declare_if_needed("force_dir_z",      rclcpp::ParameterValue(0.0));
    declare_if_needed("force_start_time", rclcpp::ParameterValue(2.0));
    declare_if_needed("force_duration",   rclcpp::ParameterValue(0.5));

    bool   force_enable = node->get_parameter("force_enable").as_bool();
    double force_mag    = node->get_parameter("force_magnitude").as_double();
    double force_dir_x  = node->get_parameter("force_dir_x").as_double();
    double force_dir_y  = node->get_parameter("force_dir_y").as_double();
    double force_dir_z  = node->get_parameter("force_dir_z").as_double();
    double force_start  = node->get_parameter("force_start_time").as_double();
    double force_dur    = node->get_parameter("force_duration").as_double();

    if (force_enable) {
        RCLCPP_INFO(node->get_logger(),
            "External force ENABLED: mag=%.2f N, dir=[%.3f,%.3f,%.3f], start=%.3f s, dur=%.3f s",
            force_mag, force_dir_x, force_dir_y, force_dir_z, force_start, force_dur);
    } else {
        RCLCPP_INFO(node->get_logger(), "External force DISABLED (conservative system)");
    }

    // load model (double) and data
    Model model;
    try {
        pinocchio::urdf::buildModel(urdf_path, model);
    } catch (const std::exception &e) {
        RCLCPP_ERROR(node->get_logger(), "Error loading URDF: %s", e.what());
        return 1;
    }
    Data data(model);
    model.gravity.linear(Eigen::Vector3d(0,0,-9.81));

    // 获取末端 frame id
    // Pinocchio 找不到 frame 时返回 model.nframes（不是 -1）
    pinocchio::FrameIndex link_tcp_id = model.getFrameId("Link7");
    RCLCPP_INFO(node->get_logger(), "link_tcp_id=%d:", (int)link_tcp_id);
    if (link_tcp_id >= (pinocchio::FrameIndex)model.nframes) {
        RCLCPP_ERROR(node->get_logger(), "TCP frame not found!");
        return 1;
    }
    RCLCPP_INFO(node->get_logger(), "Model has nq=%d nv=%d", model.nq, model.nv);

    // build AD model/data
    ModelAD model_ad = model.cast<ADScalar>();
    DataAD data_ad(model_ad);

    int n = model.nq;
    int n_steps = static_cast<int>(duration / timestep);

    // initial conditions
    Vec q_prev = Vec::Zero(n);
    for (int i = 0; i < n && i < static_cast<int>(q_init_vec.size()); ++i)
        q_prev(i) = q_init_vec[i];
    Vec v_prev = Vec::Zero(n);
    Vec tau_k = Vec::Zero(n);

    // 归一化力方向，构建 Cartesian 力向量
    Eigen::Vector3d f_dir(force_dir_x, force_dir_y, force_dir_z);
    if (f_dir.norm() > 1e-10) f_dir.normalize();
    Eigen::Vector3d f_vec = force_mag * f_dir;

    // Lambda：在仿真时刻 t、关节构型 q 处求广义外力
    auto get_tau_at = [&](double t, const Vec &q) -> Vec {
        if (force_enable && t >= force_start && t < force_start + force_dur) {
            return compute_ext_generalized_force(model, data, link_tcp_id, q, f_vec);
        }
        return Vec::Zero(n);
    };

    std::vector<Vec> q_history;
    std::vector<double> time_history;
    std::vector<double> energy_history;
    std::vector<double> delta_energy_history;
    std::vector<double> h_history;
    std::vector<double> runtimes;
    std::vector<Eigen::Vector3d> ee_history;
    std::vector<Vec> momentum_history;
    std::vector<Vec> force_torque_history;
    std::vector<Eigen::Vector3d> centroidal_lin_momentum_history;

    q_history.push_back(q_prev);
    time_history.push_back(0.0);
    h_history.push_back(timestep);

    auto t_start = high_resolution_clock::now();

    auto [ee_pos0, ee_rot0] = compute_end_effector_pose(model, data, link_tcp_id, q_prev);
    ee_history.push_back(ee_pos0);

    // initial VI step  (t = 0) — 使用正确的 VI 初始化: M*v0 + D1(q0,q1,h) = h*tau
    tau_k = get_tau_at(0.0, q_prev);
    force_torque_history.push_back(tau_k);
    auto [q_curr, info_init] = VI_init(model, data, model_ad, data_ad, q_prev, v_prev, tau_k, timestep);
    if (!info_init.converged)
        RCLCPP_WARN(node->get_logger(), "VI_init did not converge (reason=%s)", info_init.reason.c_str());
    q_history.push_back(q_curr);
    time_history.push_back(timestep);
    h_history.push_back(timestep);

    // t=0: 单点公式 T0+U0（仅用于 energy_history 记录，不作为控制器参考）
    Mat M0 = inertia_matrix(model, data, q_prev);
    double T0 = 0.5 * v_prev.dot(M0 * v_prev);
    double U0 = potential_energy(model, data, q_prev);
    double E_0 = T0 + U0;
    energy_history.push_back(E_0);    // t=0 能量（单点公式）
    delta_energy_history.push_back(0.0);  // t=0 漂移 = 0（定义）

    // t=h: 中点公式（与主循环一致）
    double E_curr = discrete_energy_numeric(model, data, q_prev, q_curr, timestep);
    double E_d    = E_curr;  // 以第一步离散能量（中点公式）为 Lyapunov 控制器参考基线
    double E_prev = E_curr;  // 用于 force-off 之后的重置
    energy_history.push_back(E_curr);     // t=dt 能量（中点公式）
    delta_energy_history.push_back(0.0);  // t=h 漂移 = 0（E[1] 定义为新基准）
    auto [ee_pos1, _ee_rot1] = compute_end_effector_pose(model, data, link_tcp_id, q_curr);
    ee_history.push_back(ee_pos1);

    double t_cur = timestep; // we have advanced to q_curr at t = timestep
    double h_next = timestep;
    double xi = 0.0; // 能量误差积分项
    bool force_was_active = false; // 外力状态跟踪，用于检测外力关断瞬间
    int step_count = 1; // 用乘法 step_count*timestep 计算力采样时刻，避免浮点累加误差

    // int max_steps = std::max((int)(duration / h_min) + 10, 1000);
    for (int step=0; step < n_steps -1  && t_cur < duration - 1e-12; ++step)
    {
        auto t0 = high_resolution_clock::now();

        // 先更新本步广义外力（用 step_count*timestep 计算时刻，避免浮点累加漂移）
        double t_step = static_cast<double>(step_count) * timestep;
        tau_k = get_tau_at(t_step, q_history[q_history.size()-1]);
        force_torque_history.push_back(tau_k);
        bool force_active_now = force_enable && (t_step >= force_start) && (t_step < force_start + force_dur);

        // 外力关断瞬间：重置积分项和能量基准，防止 windup 导致步长飙升
        bool force_just_turned_off = (force_was_active && !force_active_now);
        force_was_active = force_active_now;

        // h_history.back() = 上一步实际使用的步长 (h_prev), h_next = 本步计划步长 (h_curr)
        auto [q_next, info_adapt] = solve_q_next(
            model_ad,
            data_ad,
            q_history[q_history.size()-2],
            q_history[q_history.size()-1],
            tau_k,
            h_history.back(),  // h_prev: q_{k-1}→q_k 区间步长
            h_next             // h_curr: q_k→q_{k+1} 区间步长（本步）
        );

        if (!info_adapt.converged) {
            RCLCPP_WARN(node->get_logger(), "Solver diverged at t=%.3f, reducing step.", t_cur);
            h_next *= 0.5;
            continue;
        }

        // 计算当前步离散能量
        E_curr = discrete_energy_numeric(model, data, q_history[q_history.size()-1], q_next, h_next);

        // 本步实际使用的步长（solve_q_next 已使用 h_next，先保存再决定是否更新）
        double h_cur = h_next;

        // 改进版
        // if (force_active_now) {
        //     // 固定步长段：外力期间 h_next 保持不变，不运行 Lyapunov
        // } else {
        //     // 变步长段：Lyapunov 步长控制
        //     if (force_just_turned_off) {
        //         // 外力刚结束：重置积分项，将当前步能量设为新基准
        //         // 令 E_prev = E_curr，使第一个自由步 e_k = 0，平滑衔接
        //         xi = 0.0;
        //         E_prev = E_curr;
        //         RCLCPP_INFO(node->get_logger(),
        //             "Force OFF at t=%.4f: reset controller, E_base=%.6f", t_cur, E_curr);
        //     }
        //     double e_k = E_curr - E_prev;
        //     xi += e_k;
        //     double de_dh = compute_energy_gradient(model_ad, data_ad,
        //         q_history[q_history.size()-1], q_next, h_next);
        //     // 控制律: u = (de/dh)^+ * (-alpha * e - beta * xi)
        //     double reg = 1e-8;
        //     double u_k = (de_dh / (de_dh * de_dh + reg)) * (-alpha * e_k - beta * xi);
        //     h_next = std::clamp(h_next + u_k, 1e-5, 0.05);
        // }

        // 原版逻辑
        if (force_active_now) {
            // 固定步长段：外力期间 h_next 保持不变，不运行 Lyapunov
        } else {
            // 变步长段：Lyapunov 步长控制
            if (force_just_turned_off) {
                // 外力刚结束：重置积分项，将当前步能量设为新基准
                // 令 E_prev = E_curr，使第一个自由步 e_k = 0，平滑衔接
                xi = 0.0;
                // E_prev = E_curr;
                E_d = E_curr; // 以外力结束时的能量作为新的 Lyapunov 参考基线
                RCLCPP_INFO(node->get_logger(),
                    "Force OFF at t=%.4f: reset controller, E_base=%.6f", t_cur, E_curr);
            }
            double e_k = E_curr - E_d;
            xi += e_k;
            double de_dh = compute_energy_gradient(model_ad, data_ad,
                q_history[q_history.size()-1], q_next, h_next);
            // 控制律: u = (de/dh)^+ * (-alpha * e - beta * xi)
            double reg = 1e-8;
            double u_k = (de_dh / (de_dh * de_dh + reg)) * (-alpha * e_k - beta * xi);
            h_next = std::clamp(h_next + u_k, 1e-5, 0.05);
        }

        q_history.push_back(q_next);
        h_history.push_back(h_cur);   // 记录本步实际步长（非下步预测值）
        t_cur += h_cur;               // 时间轴推进本步实际步长
        time_history.push_back(t_cur);
        ++step_count;

        energy_history.push_back(E_curr);
        delta_energy_history.push_back(E_curr - E_0);  // 相对第一步离散能量的漂移
        // E_prev = E_curr;  // 滚动更新上一步能量

        auto [ee_pos, ee_rot] = compute_end_effector_pose(model, data, link_tcp_id, q_next);
        ee_history.push_back(ee_pos);

        // 广义动量：用 h_cur（本步实际步长）计算速度
        Vec qdot_step = (q_next - q_history[q_history.size()-2]) / h_cur;
        Vec qmid_step = 0.5 * (q_next + q_history[q_history.size()-2]);
        Vec p_step = inertia_matrix(model, data, qmid_step) * qdot_step;
        momentum_history.push_back(p_step);
        // 系统总线动量
        pinocchio::computeCentroidalMomentum(model, data, q_next, qdot_step);
        centroidal_lin_momentum_history.push_back(data.hg.linear());

        auto t1 = high_resolution_clock::now();
        double elapsed = std::chrono::duration_cast<std::chrono::duration<double>>(t1 - t0).count();
        runtimes.push_back(elapsed);

        print_progress(t_cur, duration, runtimes, h_next);
    }
    std::cout << "\n";

    auto t_end = high_resolution_clock::now();
    double total_elapsed = std::chrono::duration_cast<std::chrono::duration<double>>(t_end - t_start).count();
    double avg_time = !runtimes.empty() ? std::accumulate(runtimes.begin(), runtimes.end(), 0.0) / runtimes.size() : 0.0;
    RCLCPP_INFO(node->get_logger(), "Simulation finished, wall time: %f s, Average step time: %f ms", total_elapsed, avg_time*1e3);

    // Save CSVs into parameterized folder
    double q_init_label = q_init_vec.empty() ? 0.0 : q_init_vec[0];
    std::string params_label = std::string("q") + fmt_double_label(q_init_label)
        + std::string("_dt") + fmt_double_label(timestep)
        + std::string("_T") + fmt_double_label(duration)
        + std::string("_a") + fmt_double_label(alpha)
        + std::string("_b") + fmt_double_label(beta);
    std::string csv_dir = std::string("src/marvin_sim/csv/") + params_label + std::string("/c_atsvi/");
    std::string cmd = "mkdir -p " + csv_dir; int unused = system(cmd.c_str()); (void)unused;

    write_csv(csv_dir + "q_history.csv", q_history);
    // compute generalized momentum p = M(q_mid) * qdot for each recorded configuration
    for (size_t i = 0; i < q_history.size(); ++i)
    {
        Vec qdot;
        if (i == 0)
        {
            qdot = v_prev; // initial velocity
        }
        else
        {
            double hi = h_history[i];
            if (hi == 0.0) hi = 1e-12;
            qdot = (q_history[i] - q_history[i-1]) / hi;
        }

        Vec qmid = q_history[i];
        if (i > 0) qmid = 0.5 * (q_history[i] + q_history[i-1]);
        Mat Mmid = inertia_matrix(model, data, qmid);
        Vec p = Mmid * qdot;
        // only push if not already computed online (step i > momentum_history.size())
        if (i < 2)  // initial 2 points were not added in loop
            momentum_history.insert(momentum_history.begin() + i, p);
    }

    write_csv(csv_dir + "momentum_history.csv", momentum_history);
    write_csv(csv_dir + "force_torque_history.csv", force_torque_history);
    write_csv_3d(csv_dir + "centroidal_lin_momentum_history.csv", centroidal_lin_momentum_history);
    write_csv_scalar_series(csv_dir + "time_history.csv", time_history);
    write_csv_scalar_series(csv_dir + "energy_history.csv", energy_history);
    write_csv_scalar_series(csv_dir + "delta_energy_history.csv", delta_energy_history);
    write_csv_scalar_series(csv_dir + "h_history.csv", h_history);
    write_csv_3d(csv_dir + "ee_history.csv", ee_history);

    std::ofstream avg_time_file(csv_dir + "avg_runtime.txt");
    avg_time_file << avg_time * 1000 << std::endl;
    avg_time_file.close();

    RCLCPP_INFO(node->get_logger(), "Data saved to %s", csv_dir.c_str());

    return 0;
}
