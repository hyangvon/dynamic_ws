# w10.urdf URDF Compatibility Issue

## Problem
The w10.urdf file from SolidWorks export experiences issues when loaded with Pinocchio's kinematics library. The error manifests as:

```
Assertion `check_expression_if_real<Scalar>(isUnitary(R.transpose() * R)) && "R is not a Unitary matrix"' failed.
```

This occurs at: `pinocchio/spatial/symmetric3.hpp:565` during model casting to AD types.

## Root Cause
The w10.urdf contains complex RPY (Roll-Pitch-Yaw) angle combinations such as:
- `-1.5708 0 -1.5708` (joint3)
- `1.5708 0 0` (joint4, joint6, joint8)
- `-1.5708 0 0` (joint5, joint7)

These create numerical instability in rotation matrix calculations during Pinocchio's automatic differentiation operations.

## Solution

### Quick Fix (Recommended for now)
The code now includes an automatic fallback mechanism. If w10.urdf fails to load, it automatically switches to 7_pendulum.urdf:
```bash
ros2 run w10_sim ctsvi_w10_node
# Will attempt w10.urdf first, then fallback to 7_pendulum.urdf if loading fails
```

### Permanent Fix Required
To get w10.urdf working properly, you need to:

1. **Export URDF from SolidWorks with extended precision options**
   - Use the ROS URDF Exporter plugin
   - Enable precision options for rotation matrices
   - Verify isUnitary() check passes for all transforms

2. **Manually correct RPY values**
   - Replace compound RPY angles with simpler, element-wise definitions
   - Example: `-1.5708 0 -1.5708` might be better expressed as separate zero-rotation transforms

3. **Validate with check_urdf**
   ```bash
   check_urdf src/w10_sim/urdf/w10.urdf
   ```

4. **Test with Pinocchio directly**
   ```python
   import pinocchio as pin
   model = pin.buildModelFromUrdf("src/w10_sim/urdf/w10.urdf")
   # Check allisUnitary() for all joint placements
   ```

## Current Status
- ✅ 7_pendulum.urdf: Working perfectly
- ⚠️ w10.urdf: Has numerical stability issues (auto-fallback enabled)
- ✅ Automatic fallback: Implemented

## Next Steps
1. Regenerate w10.urdf from SolidWorks with corrected settings
2. Or manually simplify the RPY angle definitions
3. Validate with Pinocchio before committing
