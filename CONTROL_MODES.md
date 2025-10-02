# Control Modes Reference Guide

## Overview
The system uses a control mode specified in the first line of `commands.txt` to determine how to control the robot.

## Implemented Control Modes

### 1. Joint Position Control (`joint_position`)
Controls the robot by specifying target joint angles.

**Commands Format:**
```
joint_position
0.0, -0.785, 0.0, -2.356, 0.0, 1.571, 0.785
0.2, -0.785, 0.0, -2.356, 0.0, 1.571, 0.785
```

**Controller Setup:**
- Switches to `joint_impedance_controller`

**How it works:**
- Server sends 7 joint angle values (in radians)
- Client directly sets robot joint targets using `robot.set_target_joint()`
- Robot moves to the specified joint configuration

**Use when:**
- You need precise control over joint angles
- You want to avoid singularities
- You have pre-planned joint trajectories

---

### 2. End Effector Position Control (`ee_position`)
Controls the robot by specifying target end effector positions (and optionally orientations).

**Commands Format (Position Only):**
```
ee_position
0.4, 0.0, 0.5
0.5, 0.1, 0.4
```

**Commands Format (Position + Orientation):**
```
ee_position
0.45, 0.0, 0.45, 0.0, 0.785, 0.0
```

**Controller Setup:**
- Switches to `cartesian_impedance_controller`
- Loads default Cartesian impedance parameters from `config/control/default_cartesian_impedance.yaml`

**How it works:**
- Server sends 3 values (x, y, z in meters) OR 6 values (x, y, z, roll, pitch, yaw)
- Client creates target pose and uses `robot.set_target(pose=target_pose)`
- Cartesian impedance controller moves end effector to desired position

**Use when:**
- You need to position the end effector at specific Cartesian coordinates
- You're planning in task space rather than joint space
- You want to maintain or specify end effector orientation
- You want smooth Cartesian space motion with impedance control

**Advantages over IK:**
- More natural Cartesian space behavior
- Better handling of singularities through impedance control
- No IK failures

---

## Future Control Modes (Not Yet Implemented)

### 3. Joint Velocity Control (`joint_velocity`)
Would control joint velocities directly.
- Format: 7 velocity values (rad/s)
- Requires switching to velocity controller

### 4. End Effector Velocity Control (`ee_velocity`)
Would control end effector velocities.
- Format: 6 velocity values (linear + angular)
- Useful for smooth Cartesian motions

### 5. Joint Torque Control (`joint_torque`)
Would control joint torques directly.
- Format: 7 torque values (Nm)
- Requires switching to torque controller
- Useful for compliant control and force control

### 6. End Effector Force Control (`ee_force`)
Would control forces at the end effector.
- Format: 6 force/torque values
- Useful for contact tasks and assembly

---

## Switching Between Control Modes

To switch control modes:
1. Stop both server and client programs
2. Edit `commands.txt` - change the first line to desired mode
3. Update command values to match the new mode's format
4. Restart client first, then server

## Example Files

- `commands.txt` - Joint position control example (default)
- `commands_ee_example.txt` - End effector position control example

