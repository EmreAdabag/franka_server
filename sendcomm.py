"""UDP Server - Sends target joint positions from a text file."""
import socket
import time
import json


class RobotCommandServer:
    """UDP Server class for sending commands to and receiving states from a Franka robot."""
    
    def __init__(self, server_host='0.0.0.0', server_port=5000, verbose=True):
        """Initialize the robot command server.
        
        Args:
            server_host: Host address to bind the server socket (default: '0.0.0.0')
            server_port: Port number for the server socket (default: 5000)
            verbose: Enable verbose output (default: True)
        """
        self.server_host = server_host
        self.server_port = server_port
        self.verbose = verbose
        
        # Initialize UDP socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.server_host, self.server_port))
        
        # Store latest robot states from client
        self.robot_states = {
            'joint_positions': [],
            'joint_velocities': [],
            'joint_efforts': [],
            'ee_position': [],
            'ee_orientation': []
        }
        
        # Store client address and control mode
        self.client_address = None
        self.control_mode = None
        
        if self.verbose:
            print(f"Server listening on {self.server_host}:{self.server_port}")
    
    def read_commands_file(self, filename):
        """Read commands from text file.
        
        First line specifies control mode:
        - joint_position: Control joint positions (7 values)
        - ee_position: Control end effector position (3 or 6 values: x,y,z or x,y,z,roll,pitch,yaw)
        - joint_velocity: Control joint velocities (7 values) [NOT IMPLEMENTED YET]
        - ee_velocity: Control end effector velocity (6 values) [NOT IMPLEMENTED YET]
        - joint_torque: Control joint torques (7 values) [NOT IMPLEMENTED YET]
        - ee_force: Control end effector forces (6 values) [NOT IMPLEMENTED YET]
        
        Subsequent lines contain the command values.
        
        Args:
            filename: Path to the commands file
            
        Returns:
            tuple: (control_mode, list of command arrays)
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
    
    def wait_for_handshake(self, control_mode=None):
        """Wait for client connection and complete handshake.
        
        Args:
            control_mode: Control mode to send to client (optional, can be set later)
            
        Returns:
            tuple: (client_address, handshake_message)
        """
        if self.verbose:
            print("Waiting for client connection...")
        
        data, self.client_address = self.sock.recvfrom(1024)
        handshake_msg = json.loads(data.decode())
        
        if self.verbose:
            print(f"Client connected from {self.client_address}: {handshake_msg}")
        
        # Send control mode if provided
        if control_mode:
            self.control_mode = control_mode
            handshake_response = json.dumps({'type': 'handshake', 'control_mode': control_mode})
            self.sock.sendto(handshake_response.encode(), self.client_address)
            if self.verbose:
                print(f"Sent control mode to client: {control_mode}")
        
        return self.client_address, handshake_msg
    
    def send_command(self, control_mode, command_values, client_addr=None):
        """Send command to client via UDP based on control mode.
        
        Args:
            control_mode: Type of command ('joint_position', 'ee_position', etc.)
            command_values: List of command values
            client_addr: Client address (optional, uses stored address if None)
        """
        if client_addr is None:
            client_addr = self.client_address
        
        if client_addr is None:
            raise ValueError("No client address available. Complete handshake first.")
        
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
        
        if self.verbose:
            print(f"Sent {control_mode}: {command_values}")
        
        self.sock.sendto(message.encode(), client_addr)
    
    def receive_state(self, timeout=5.0):
        """Receive and process robot states from client.
        
        Args:
            timeout: Socket timeout in seconds (default: 5.0)
            
        Returns:
            dict: Robot states dictionary or None if timeout
        """
        self.sock.settimeout(timeout)
        
        try:
            data, addr = self.sock.recvfrom(4096)  # Larger buffer for state data
            
            try:
                message = json.loads(data.decode())
                
                if message.get('type') == 'robot_states':
                    self.robot_states = message['data']
                    
                    if self.verbose:
                        # Print received states in readable format
                        print("\n=== Received Robot States ===")
                        print(f"Joint Positions: {self.robot_states['joint_positions']}")
                        print(f"Joint Velocities: {self.robot_states['joint_velocities']}")
                        print(f"Joint Efforts (Torques): {self.robot_states['joint_efforts']}")
                        print(f"End Effector Pose: {self.robot_states['ee_pose']}")
                        print(f"End Effector Position: {self.robot_states['ee_position']}")
                        print(f"End Effector Orientation (Rotation Matrix):")
                        for row in self.robot_states['ee_orientation']:
                            print(f"  {row}")
                        print("============================\n")
                    
                    return self.robot_states
                else:
                    if self.verbose:
                        print(f"Received unexpected message type: {message.get('type')}")
                    return None
                    
            except Exception as e:
                print(f"Error processing robot states: {e}")
                return None
                
        except socket.timeout:
            if self.verbose:
                print("Warning: No response from client (timeout)")
            return None
    
    def get_latest_state(self):
        """Get the most recently received robot state.
        
        Returns:
            dict: Latest robot states dictionary
        """
        return self.robot_states
    
    def close(self):
        """Close the server socket."""
        self.sock.close()
        if self.verbose:
            print("Server socket closed")


# Main loop (for backward compatibility)
def main():
    """Example usage of RobotCommandServer class."""
    commands_file = 'commands_ee_example.txt'
    
    # Initialize server
    server = RobotCommandServer(server_host='0.0.0.0', server_port=5000, verbose=True)
    
    try:
        # Read control mode and commands from file
        control_mode, commands = server.read_commands_file(commands_file)
        print(f"Control mode: {control_mode}")
        print(f"Loaded {len(commands)} commands from file")
        
        # Wait for client handshake
        server.wait_for_handshake(control_mode)
        
        # Send commands one by one
        for command in commands:
            server.send_command(control_mode, command)
            time.sleep(2.0)  # Wait between commands
            
            # Receive robot states from client
            server.receive_state(timeout=5.0)
        
        print("All commands sent successfully")
        
    except KeyboardInterrupt:
        print("\nServer shutting down...")
    finally:
        server.close()


if __name__ == "__main__":
    main()