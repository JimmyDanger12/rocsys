import socket

robot_ip = '192.168.137.5'  # Replace with the robot's IP address or hostname
robot_port = 7000  # Replace with the port number configured on the robot

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((robot_ip, robot_port))
print("Connected")

drl_command = 'move_home(DR_HOME_TARGET_USER)'  # Replace with your actual DRL command
client_socket.sendall(drl_command.encode())
print(f"Command {drl_command} sent")

client_socket.close()
