# UDP Communication Data Format

## Initial Handshake

### Client → Server
```json
{
    "status": "ready"
}
```

### Server → Client (Handshake Response)
```json
{
    "type": "handshake",
    "control_mode": "joint_position"  // or "ee_position", "joint_velocity", etc.
}
```

## Command Messages (Server → Client)

### Joint Position Command
```json
{
    "type": "joint_position",
    "data": [j1, j2, j3, j4, j5, j6, j7]  // radians
}
```

### End Effector Position Command
```json
{
    "type": "ee_position",
    "data": [x, y, z]  // meters, keeps current orientation
}
```
or
```json
{
    "type": "ee_position",
    "data": [x, y, z, roll, pitch, yaw]  // meters + radians
}
```

### Future Commands (Not Implemented)
- `"type": "joint_velocity"` with 7 velocity values
- `"type": "ee_velocity"` with 6 velocity values
- `"type": "joint_torque"` with 7 torque values
- `"type": "ee_force"` with 6 force values

## Robot State Feedback (Client → Server)
```json
{
    "type": "robot_states",
    "data": {
        "joint_positions": [j1, j2, j3, j4, j5, j6, j7],
        "joint_velocities": [v1, v2, v3, v4, v5, v6, v7],
        "joint_efforts": [e1, e2, e3, e4, e5, e6, e7],
        "ee_position": [x, y, z],
        "ee_orientation": [
            [r11, r12, r13],
            [r21, r22, r23],
            [r31, r32, r33]
        ]
    }
}
```

## Communication Flow

1. **Client sends handshake** to server with `{'status': 'ready'}`
2. **Server sends control mode** to client in handshake response
3. **Server sends command** based on control mode
4. **Client executes command** (moves robot)
5. **Client sends complete robot state** back to server
6. **Server stores state** in global `robot_states` variable
7. Repeat steps 3-6 for each command in `commands.txt`

## Accessing Data on Server

The server maintains a global variable `robot_states` that always contains the most recently received robot state:

```python
# Example: Access the latest robot state
print(f"Current joint positions: {robot_states['joint_positions']}")
print(f"Current EE position: {robot_states['ee_position']}")
print(f"Current joint torques: {robot_states['joint_efforts']}")
```

