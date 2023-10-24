from DRCF import *
import socket

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind(('0.0.0.0', 7005))  # Replace with appropriate IP and port
server_socket.listen(1)

print('Server listening for connections...')
server_socket.settimeout(120)  # Set initial timeout to x seconds

change_operation_speed(50)      

while True:
    try:
        client_socket, client_address = server_socket.accept()
        print('Connection established with:', client_address)

        while True:
            command = client_socket.recv(1024).decode("utf-8")  # Receive DRL command from client
            if not command:
                # If no command is received, the client has closed the connection
                print('Client closed the connection.')
                break
            
            # Execute the DRL command on the robot
            exec(command)
            wait(0.5)

            current_pos = str(get_current_posx())
            # Send "received" message back to the client
            client_socket.sendall(current_pos.encode("utf-8"))

    except socket.timeout:
        # Handle timeout exception, meaning no new messages received for 60 seconds
        print("No connection to socket for 60 seconds. Server shutting down.")
        break

    finally:
        client_socket.close()
        server_socket.close()
