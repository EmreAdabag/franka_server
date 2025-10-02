"""UDP Server - Sends target joint positions from a text file."""
import socket
import time
import json

# Server configuration
SERVER_HOST = '0.0.0.0'  # Listen on all network interfaces
SERVER_PORT = 5000
CLIENT_PORT = 5001  # Port for receiving messages (for future 2-way communication)
VERBOSE = True
commands_file = 'commands_ee_example.txt'

# Initialize UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((SERVER_HOST, SERVER_PORT))
print(f"Server listening on {SERVER_HOST}:{SERVER_PORT}")

# Global variable to store latest robot states from client
robot_states = {
    'joint_positions': [],
    'joint_velocities': [],
    'joint_efforts': [],
    'ee_position': [],
    'ee_orientation': []
}

# For future 2-way communication: store client address when first message is received
client_address = None


def read_commands_file(filename):
    """Read commands from text file.
    
    First line specifies control mode:
    - joint_position: Control joint positions (7 values)
    - ee_position: Control end effector position (3 or 6 values: x,y,z or x,y,z,roll,pitch,yaw)
    - joint_velocity: Control joint velocities (7 values) [NOT IMPLEMENTED YET]
    - ee_velocity: Control end effector velocity (6 values) [NOT IMPLEMENTED YET]
    - joint_torque: Control joint torques (7 values) [NOT IMPLEMENTED YET]
    - ee_force: Control end effector forces (6 values) [NOT IMPLEMENTED YET]
    
    Subsequent lines contain the command values.
    """
    control_mode = None
    commands = []
    
    with open(filename, 'r') as f:
        for i, line in enumerate(f):
            line = line.strip()
            if line and not line.startswith('#'):  # Skip empty lines and comments
                if i == 0 or control_mode is None:
                    # First non-comment line is the control mode
                    control_mode = line.lower()
                else:
                    # Parse command values
                    values = [float(x.strip()) for x in line.split(',')]
                    commands.append(values)
    
    return control_mode, commands


def send_command(control_mode, command_values, client_addr):
    """Send command to client via UDP based on control mode."""
    if control_mode == 'joint_position':
        message = json.dumps({'type': 'joint_position', 'data': command_values})
    elif control_mode == 'ee_position':
        message = json.dumps({'type': 'ee_position', 'data': command_values})
    elif control_mode == 'joint_velocity':
        message = json.dumps({'type': 'joint_velocity', 'data': command_values})

    elif control_mode == 'ee_velocity':
        message = json.dumps({'type': 'ee_velocity', 'data': command_values})

    elif control_mode == 'joint_torque':
        message = json.dumps({'type': 'joint_torque', 'data': command_values})

    elif control_mode == 'ee_force':
        message = json.dumps({'type': 'ee_force', 'data': command_values})

    else:
        raise ValueError(f"Unknown control mode: {control_mode}")
    print(f"Sent {control_mode}: {command_values}")
    sock.sendto(message.encode(), client_addr)


def process_robot_states(data):
    """Process and store robot states received from client."""
    global robot_states
    
    try:
        message = json.loads(data.decode())
        
        if message.get('type') == 'robot_states':
            robot_states = message['data']
            if VERBOSE:
                # Print received states in readable format
                print("\n=== Received Robot States ===")
                print(f"Joint Positions: {robot_states['joint_positions']}")
                print(f"Joint Velocities: {robot_states['joint_velocities']}")
                print(f"Joint Efforts (Torques): {robot_states['joint_efforts']}")
                print(f"End Effector Pose: {robot_states['ee_pose']}")
                print(f"End Effector Position: {robot_states['ee_position']}")
                print(f"End Effector Orientation (Rotation Matrix):")
                for row in robot_states['ee_orientation']:
                    print(f"  {row}")
                print("============================\n")
    except Exception as e:
        print(f"Error processing robot states: {e}")


# Main loop
def main():
    # Read control mode and commands from file
    control_mode, commands = read_commands_file(commands_file)
    print(f"Control mode: {control_mode}")
    print(f"Loaded {len(commands)} commands from file")
    
    # Wait for initial handshake from client
    print("Waiting for client connection...")
    data, client_address = sock.recvfrom(1024)
    handshake_msg = json.loads(data.decode())
    print(f"Client connected from {client_address}: {handshake_msg}")
    
    # Send control mode to client in handshake response
    handshake_response = json.dumps({'type': 'handshake', 'control_mode': control_mode})
    sock.sendto(handshake_response.encode(), client_address)
    print(f"Sent control mode to client: {control_mode}")
    
    # Send commands one by one
    try:
        for command in commands:
            send_command(control_mode, command, client_address)
            time.sleep(2.0)  # Wait between commands
            
            # Receive robot states from client
            sock.settimeout(5.0)  # 5 second timeout
            try:
                data, addr = sock.recvfrom(4096)  # Larger buffer for state data
                process_robot_states(data)
            except socket.timeout:
                print("Warning: No response from client (timeout)")
        
        print("All commands sent successfully")
    except KeyboardInterrupt:
        print("\nServer shutting down...")
    finally:
        sock.close()


if __name__ == "__main__":
    main()