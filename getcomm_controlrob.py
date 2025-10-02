"""UDP Client - Receives commands and controls Franka robot."""
import socket
import json
import numpy as np

from crisp_py.robot import Robot
from crisp_py.robot_config import FrankaConfig

# Client configuration
SERVER_HOST = '192.168.2.53'  # Server computer IP address
SERVER_PORT = 5000
CLIENT_PORT = 5001
VERBOSE = True

# Initialize UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(('0.0.0.0', CLIENT_PORT))
print(f"Client started on port {CLIENT_PORT}")

# Initialize robot (following crisp_py example)
robot_config = FrankaConfig(publish_frequency=100.0, target_joint_topic="target_joint")
robot = Robot(namespace="")
robot.wait_until_ready()
print("Robot ready")

# Global variable to store current control mode
control_mode = None


def send_handshake():
    """Send initial handshake to server."""
    message = json.dumps({'status': 'ready'})
    sock.sendto(message.encode(), (SERVER_HOST, SERVER_PORT))
    print(f"Sent handshake to {SERVER_HOST}:{SERVER_PORT}")


def receive_control_mode():
    """Receive control mode from server during handshake."""
    global control_mode
    data, addr = sock.recvfrom(1024)
    message = json.loads(data.decode())
    
    if message.get('type') == 'handshake':
        control_mode = message['control_mode']
        print(f"Received control mode: {control_mode}")
        return control_mode
    else:
        raise ValueError("Expected handshake message from server")


def configure_robot_for_control_mode(mode):
    """Configure robot controller based on control mode."""
    if mode == 'joint_position':
        # Use joint impedance controller for joint position control
        robot.controller_switcher_client.switch_controller("joint_impedance_controller")
        print("Switched to joint_impedance_controller")
        
    elif mode == 'ee_position':
        # Use Cartesian impedance controller for end effector position control
        robot.controller_switcher_client.switch_controller("cartesian_impedance_controller")
        robot.cartesian_controller_parameters_client.load_param_config(
            file_path="config/control/default_cartesian_impedance.yaml"
        )
        print("Switched to cartesian_impedance_controller with default parameters")
        
    elif mode == 'joint_velocity':
        # TODO: Implement velocity controller setup
        print("Joint velocity control not fully implemented yet")
        robot.controller_switcher_client.switch_controller("joint_impedance_controller")
        
    elif mode == 'ee_velocity':
        # TODO: Implement EE velocity controller setup
        print("EE velocity control not fully implemented yet")
        robot.controller_switcher_client.switch_controller("cartesian_impedance_controller")
        
    elif mode == 'joint_torque':
        # TODO: Implement torque controller setup
        print("Joint torque control not fully implemented yet")
        robot.controller_switcher_client.switch_controller("joint_impedance_controller")
        
    elif mode == 'ee_force':
        # TODO: Implement force controller setup
        print("EE force control not fully implemented yet")
        robot.controller_switcher_client.switch_controller("cartesian_impedance_controller")
        
    else:
        raise ValueError(f"Unknown control mode: {mode}")


def receive_command():
    """Receive command from server."""
    data, addr = sock.recvfrom(1024)
    message = json.loads(data.decode())
    return message


def get_robot_states():
    """Collect current robot states including joint states and end effector pose."""
    # Get joint states (position, velocity, effort/torque)
    joint_positions = robot.joint_values.tolist()
    joint_velocities = []
    joint_efforts = []
    # joint_velocities = robot.joint_velocities.tolist()
    # joint_efforts = robot.joint_efforts.tolist()
    
    # Get end effector pose (position and orientation)
    ee_pose = str(robot.end_effector_pose)
    ee_position = []
    ee_orientation = []
    # ee_position = ee_pose[:3, 3].tolist()  # Extract position from transformation matrix
    # ee_orientation = ee_pose[:3, :3].tolist()  # Extract rotation matrix
    
    return {
        'joint_positions': joint_positions,
        'joint_velocities': joint_velocities,
        'joint_efforts': joint_efforts,
        'ee_pose': ee_pose,
        'ee_position': ee_position,
        'ee_orientation': ee_orientation
    }


def send_robot_states():
    """Send current robot states back to server."""
    robot_states = get_robot_states()
    message = json.dumps({'type': 'robot_states', 'data': robot_states})
    sock.sendto(message.encode(), (SERVER_HOST, SERVER_PORT))
    
    if VERBOSE:
        # Print readable format
        print("\n=== Sent Robot States ===")
        print(f"Joint Positions: {robot_states['joint_positions']}")
        print(f"Joint Velocities: {robot_states['joint_velocities']}")
        print(f"Joint Efforts: {robot_states['joint_efforts']}")
        print(f"EE Position: {robot_states['ee_position']}")
        print("========================\n")


def execute_joint_position_command(target_joints):
    """Execute joint position command."""
    print(f"Executing joint position command: {target_joints}")
    robot.set_target_joint(np.array(target_joints))


def execute_ee_position_command(target_ee_pos):
    """Execute end effector position command.
    
    Args:
        target_ee_pos: List of 3 values [x, y, z] or 6 values [x, y, z, roll, pitch, yaw]
    """
    print(f"Executing EE position command: {target_ee_pos}")
    
    if len(target_ee_pos) == 3:
        # Only position provided, keep current orientation
        current_ee_pose = robot.end_effector_pose.copy()
        target_pose = current_ee_pose
        target_pose.position = np.array(target_ee_pos)
        
    elif len(target_ee_pos) == 6:
        # Position + orientation (roll, pitch, yaw) provided
        x, y, z, roll, pitch, yaw = target_ee_pos
        
        # Create rotation matrix from roll, pitch, yaw
        from scipy.spatial.transform import Rotation
        rotation = Rotation.from_euler('xyz', [roll, pitch, yaw])
        # rotation_matrix = rotation.as_matrix()
        
        # Create pose with position and orientation
        current_ee_pose = robot.end_effector_pose.copy()
        target_pose = current_ee_pose
        target_pose.position = np.array([x, y, z])
        target_pose.orientation = rotation
    else:
        raise ValueError(f"EE position command must have 3 or 6 values, got {len(target_ee_pos)}")
    
    # Use Cartesian controller to set target pose directly
    # This uses the cartesian_impedance_controller to move to the target
    robot.set_target(pose=target_pose)


# Main loop
def main():
    global control_mode
    
    try:
        # Send handshake to establish connection
        send_handshake()
        
        # Receive control mode from server
        control_mode = receive_control_mode()
        
        # Configure robot based on control mode
        configure_robot_for_control_mode(control_mode)
        
        # Main command loop
        print(f"Waiting for {control_mode} commands from server...")
        while True:
            # Receive command
            message = receive_command()
            command_type = message.get('type')
            command_data = message.get('data')
            
            # Execute command based on type
            if command_type == 'joint_position':
                execute_joint_position_command(command_data)
                
            elif command_type == 'ee_position':
                execute_ee_position_command(command_data)
                
            elif command_type == 'joint_velocity':
                print("Joint velocity control not implemented yet")
                
            elif command_type == 'ee_velocity':
                print("EE velocity control not implemented yet")
                
            elif command_type == 'joint_torque':
                print("Joint torque control not implemented yet")
                
            elif command_type == 'ee_force':
                print("EE force control not implemented yet")
                
            else:
                print(f"Unknown command type: {command_type}")
            
            # Send current robot states back to server
            send_robot_states()
            
    except KeyboardInterrupt:
        print("\nClient shutting down...")
    finally:
        robot.shutdown()
        sock.close()
        print("Robot shutdown complete")


if __name__ == "__main__":
    main()
