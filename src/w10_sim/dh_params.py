# w10机械臂 DH参数
# 自动生成 - 需要手工验证

DH_PARAMS = {
    'joint2': {
        'index': 1,
        'theta': 0.000000,  # Joint angle (rad) - 由运动规划确定
        'd': 0.163000,        # Link offset (m)
        'a': 0.000000,        # Link length (m)
        'alpha': 0.000000,  # Link twist (rad)
    },
    'joint3': {
        'index': 2,
        'theta': 0.000000,  # Joint angle (rad) - 由运动规划确定
        'd': 0.085000,        # Link offset (m)
        'a': 0.000000,        # Link length (m)
        'alpha': 0.000000,  # Link twist (rad)
    },
    'joint4': {
        'index': 3,
        'theta': 0.000000,  # Joint angle (rad) - 由运动规划确定
        'd': 0.000089,        # Link offset (m)
        'a': 0.281500,        # Link length (m)
        'alpha': 0.000000,  # Link twist (rad)
    },
    'joint5': {
        'index': 4,
        'theta': 0.000000,  # Joint angle (rad) - 由运动规划确定
        'd': 0.143500,        # Link offset (m)
        'a': 0.050005,        # Link length (m)
        'alpha': 0.000000,  # Link twist (rad)
    },
    'joint6': {
        'index': 5,
        'theta': 0.000000,  # Joint angle (rad) - 由运动规划确定
        'd': 0.000012,        # Link offset (m)
        'a': 0.121284,        # Link length (m)
        'alpha': 0.000000,  # Link twist (rad)
    },
    'joint7': {
        'index': 6,
        'theta': 0.000000,  # Joint angle (rad) - 由运动规划确定
        'd': 0.316200,        # Link offset (m)
        'a': 0.062949,        # Link length (m)
        'alpha': 0.000000,  # Link twist (rad)
    },
    'joint8': {
        'index': 7,
        'theta': 0.000000,  # Joint angle (rad) - 由运动规划确定
        'd': 0.062000,        # Link offset (m)
        'a': 0.068400,        # Link length (m)
        'alpha': 0.000000,  # Link twist (rad)
    },
}

# DH变换矩阵 (标准形式)
# T[i] = Rz(theta) * Tz(d) * Tx(a) * Rx(alpha)
