# w10机械臂 DH参数提取与URDF重建指南

## 快速开始

### 1. 从w10.urdf导出DH参数

```bash
cd ~/ros2_ws/dynamic_ws
python3 src/w10_sim/scripts/extract_dh_params.py
```

这会生成以下文件：
- **dh_params.csv** - Excel/表格格式
- **dh_params.py** - Python字典格式
- **dh_params.md** - Markdown表格
- **dh_params.tex** - LaTeX文档格式

### 2. w10的DH参数表

| 关节 | θ (rad) | d (m) | a (m) | α (rad) | 轴向 |
|------|---------|-------|-------|---------|------|
| joint2 | 0.0000 | 0.1630 | 0.0000 | 0.0000 | (0,0,-1) |
| joint3 | 0.0000 | 0.0850 | 0.0000 | 0.0000 | (0,0,-1) |
| joint4 | 0.0000 | 0.0001 | 0.2815 | 0.0000 | (0,0,-1) |
| joint5 | 0.0000 | 0.1435 | 0.0500 | 0.0000 | (0,0,-1) |
| joint6 | 0.0000 | 0.0000 | 0.1213 | 0.0000 | (0,0,-1) |
| joint7 | 0.0000 | 0.3162 | 0.0629 | 0.0000 | (0,0,-1) |
| joint8 | 0.0000 | 0.0620 | 0.0684 | 0.0000 | (0,0,-1) |

### 3. DH参数含义

- **θ (theta)**: 关节旋转角度（由运动规划控制，初始=0）
- **d**: 关节宽度（沿Z轴的偏移）
- **a**: 链接长度（沿X轴）
- **α (alpha)**: 链接间的扭转角（绕X轴）

## 从DH参数生成规范URDF

### 方法1：使用自动脚本（推荐）

```bash
python3 src/w10_sim/scripts/generate_urdf_from_dh.py
```

这会生成：`src/w10_sim/urdf/w10_canonical.urdf`

**特点**：
- ✓ Pinocchio完全兼容
- ✓ 所有关节为标准Z轴旋转
- ✓ RPY和xyz自DH参数计算
- ✓ 使用简化几何（圆柱体而非复杂mesh）

### 方法2：手工文件编辑（学习用）

URDF中，DH参数转换为origin的映射：

```
DH参数 → URDF origin:
theta    → 关节的旋转（由<axis>和运动控制）
d        → origin xyz="0 0 d"
a        → origin xyz="a 0 0"
alpha    → origin rpy="alpha 0 0"
```

示例（joint2从DH转为URDF）：
```xml
<joint name="joint2" type="revolute">
  <!-- DH: theta=0, d=0.163, a=0, alpha=0 -->
  <origin xyz="0 0 0.163" rpy="0 0 0" />
  <axis xyz="0 0 1" />
</joint>
```

## 验证新URDF

### 测试1：加载检验
```bash
python3 -c "import pinocchio as pin; m = pin.buildModelFromUrdf('src/w10_sim/urdf/w10_canonical.urdf'); print(f'成功: {m.njoints}个关节')"
```

### 测试2：运行仿真
```bash
# 编译
colcon build --packages-select w10_sim

# 运行（使用新URDF）
ros2 launch w10_sim ctsvi_w10.launch.py \
    --ros-args -p urdf_path:=$PWD/src/w10_sim/urdf/w10_canonical.urdf

# 或使用参数文件方式
ros2 run w10_sim ctsvi_w10_node \
    --ros-args -p urdf_path:=src/w10_sim/urdf/w10_canonical.urdf
```

### 测试3：查看仿真结果
```bash
# 查看生成的CSV数据
ls -lh src/w10_sim/csv/*/ctsvi_w10/*.csv | head -5

# 分析结果
python3 src/w10_sim/scripts/analyze_vi_results.py \
    --path src/w10_sim/csv/q0p1_dt0p01_T1_0_0/ctsvi_w10/
```

## 文件说明

### 生成的文件位置

```
src/w10_sim/
├── dh_params.csv           # DH参数CSV表
├── dh_params.py            # Python字典格式
├── dh_params.md            # Markdown参考
├── dh_params.tex           # LaTeX表格
├── urdf/
│   ├── w10.urdf            # 原始URDF (SolidWorks导出，Pinocchio不兼容)
│   ├── w10.urdf.bak        # 第一个修改版本备份
│   ├── w10.urdf.complex    # 简化后的版本备份
│   ├── w10_canonical.urdf  # ✓ 规范版本（推荐使用）
│   └── 7_pendulum.urdf     # 参考实现（已验证）
└── scripts/
    ├── extract_dh_params.py      # DH提取工具
    └── generate_urdf_from_dh.py  # URDF生成工具
```

## 常见问题

### Q: 为什么原始w10.urdf会导致Pinocchio错误？
**A**: SolidWorks导出的URDF包含复杂的RPY组合，这些在Pinocchio的自动微分（AD）引擎中会产生数值不稳定的旋转矩阵。规范版本避免了这种问题。

### Q: 规范URDF和原始URDF的运动学是否相同？
**A**: **不完全相同**。规范URDF基于DH参数，代表标准的关节配置，但可能与实际SolidWorks模型的网格不同。质量参数也是估计值。

### Q: 如何调整规范URDF使其更准确？
**A**: 编辑 `generate_urdf_from_dh.py` 中的参数：
- 修改 `dh_table` 数组更新DH参数
- 调整质量值和惯性张量
- 修改link的几何形状（不一定要用圆柱体）

## 下一步

1. **运行仿真验证工作**
   ```bash
   ros2 launch w10_sim ctsvi_w10.launch.py --ros-args -p urdf_path:=$PWD/src/w10_sim/urdf/w10_canonical.urdf
   ```

2. **从实际硬件获取精确DH参数**
   - 测量各关节间距
   - 验证轴向方向
   - 称量各linkb的质量
   - 测量惯性张量

3. **微调URDF参数**
   - 基于实验数据更新DH参数
   - 重新生成URDF
   - 对比仿真与实验结果

4. **GitHub提交**
   ```bash
   git add src/w10_sim/dh_params* src/w10_sim/urdf/w10_canonical.urdf
   git commit -m "Add: w10 DH parameters and canonical URDF"
   git push origin main
   ```

## 参考命令速查表

```bash
# 提取DH参数
python3 src/w10_sim/scripts/extract_dh_params.py

# 生成规范URDF
python3 src/w10_sim/scripts/generate_urdf_from_dh.py

# 查看DH参数（Markdown）
cat src/w10_sim/dh_params.md

# 查看DH参数（Python）
python3 -c "exec(open('src/w10_sim/dh_params.py').read()); print(DH_PARAMS)"

# 查看DH参数（CSV）
column -t -s, src/w10_sim/dh_params.csv | less

# 构建并测试
colcon build --packages-select w10_sim && \
ros2 launch w10_sim ctsvi_w10.launch.py --ros-args -p urdf_path:=$PWD/src/w10_sim/urdf/w10_canonical.urdf
```

---
**最后更新**: 2026-03-31
**DH提取工具版本**: 1.0
