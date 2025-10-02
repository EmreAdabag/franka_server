# UDP Robot Control System for Franka Robot

This system enables sending robot commands from a server computer to a client controlling a Franka robot via UDP. Supports multiple control modes including joint position and end effector position control.

## Files

- **`vik_sendcomm.py`**: Server script that sends commands from a text file
- **`vik_getcomm_controlrob.py`**: Client script that receives commands and controls the robot
- **`commands.txt`**: Text file containing control mode and command values
- **`commands_ee_example.txt`**: Example file for end effector position control
- **`requirements.txt`**: Python dependencies
- **`DATA_FORMAT.md`**: Detailed communication protocol documentation

## Setup

### Server Computer (sends commands)
```bash
pip install -r requirements.txt
```

### Robot Computer (controls robot)
```bash
pip install -r requirements.txt
pip install git+https://github.com/utiasDSL/crisp_py.git
```

## Configuration

1. **Edit `vik_getcomm_controlrob.py`**: Set `SERVER_HOST` to your server's IP address (currently set to `192.168.2.53`)

2. **Edit `commands.txt`**: 
   - **First line**: Specify control mode (`joint_position` or `ee_position`)
   - **Subsequent lines**: Add command values based on the control mode

## Usage

### Step 1: Start the client (on robot computer at 192.168.2.102)
```bash
python vik_getcomm_controlrob.py
```

### Step 2: Start the server (on separate computer at 192.168.2.53)
```bash
python vik_sendcomm.py
```

The server will:
1. Send the control mode to the client during handshake
2. Send commands one by one based on the control mode
3. Receive and display robot state feedback after each command

**Note:** The client automatically configures the robot controller based on the received control mode:
- `joint_position` → switches to `joint_impedance_controller`
- `ee_position` → switches to `cartesian_impedance_controller` with default parameters

## Control Modes

The system supports multiple control modes (specified in first line of `commands.txt`):

### ✅ Implemented:
- **`joint_position`**: Control joint positions (7 values: j1-j7 in radians)
  - Uses `joint_impedance_controller`
- **`ee_position`**: Control end effector position
  - Uses `cartesian_impedance_controller`
  - 3 values: `x, y, z` (meters) - keeps current orientation
  - 6 values: `x, y, z, roll, pitch, yaw` (meters + radians)

### 🚧 Future Implementation:
- **`joint_velocity`**: Control joint velocities (7 values in rad/s)
- **`ee_velocity`**: Control end effector velocity (6 values)
- **`joint_torque`**: Control joint torques (7 values in Nm)
- **`ee_force`**: Control end effector forces (6 values)

## 2-Way Communication

### From Server to Client:
- Control mode (during handshake)
- Commands based on control mode

### From Client to Server:
- **Joint States**: Current positions, velocities, and efforts/torques (7 values each)
- **End Effector State**: Position (x, y, z) and orientation (3x3 rotation matrix)

All robot state data is stored in the global variable `robot_states` on the server for easy access.

### Accessing Robot States on Server

The `robot_states` global variable contains:
```python
{
    'joint_positions': [j1, j2, j3, j4, j5, j6, j7],        # radians
    'joint_velocities': [v1, v2, v3, v4, v5, v6, v7],       # rad/s
    'joint_efforts': [e1, e2, e3, e4, e5, e6, e7],          # torques (Nm)
    'ee_position': [x, y, z],                                # meters
    'ee_orientation': [[r11, r12, r13],                      # 3x3 rotation matrix
                       [r21, r22, r23],
                       [r31, r32, r33]]
}
```

You can access this variable from anywhere in the server script to read the latest robot state.

## Commands File Format

The `commands.txt` file structure:

1. **First non-comment line**: Control mode
   ```
   joint_position
   ```
   or
   ```
   ee_position
   ```

2. **Subsequent lines**: Command values (comma-separated)

### Joint Position Commands
```
# First line: control mode
joint_position

# Commands: 7 values per line (radians)
0.0, -0.785, 0.0, -2.356, 0.0, 1.571, 0.785
0.2, -0.785, 0.0, -2.356, 0.0, 1.571, 0.785
```

### End Effector Position Commands
```
# First line: control mode
ee_position

# Commands: 3 values (x, y, z in meters)
0.4, 0.0, 0.5
0.5, 0.1, 0.4

# Or 6 values (x, y, z in meters, roll, pitch, yaw in radians)
0.45, 0.0, 0.45, 0.0, 0.785, 0.0
```

Lines starting with `#` are treated as comments.

