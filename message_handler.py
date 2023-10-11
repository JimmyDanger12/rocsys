import logging
import socket
from robot_controller import RobotController
from roc_logging import get_logger

CMD_HOME = "move_home"
CMD_SOCKET_DET = "socket_detection"
CMD_UNPLUG = "start_unplug"
MSG_SAFETY = "safety_detection"
MSG_CONTAINER_DOWN = "container_down"
MSG_UNKNOWN_RESPONSE = "unknown_response"

RES_FAIL = 0
RES_SUCCESS = 1
RES_UNRELIABLE = 2

RES_START = 1
RES_END = 2
RES_FOREIGN = 0

class MessageHandler():
    """
    This class handles the management of the robot commands 
    and relays them to the robot

    """

    def __init__(self, server, robot_controller:RobotController):
        self.server = server
        self.robot_controller = robot_controller
        self.robot_controller.message_handler = self
        self.robot_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.robot_socket.settimeout(60)
        try:
            self.robot_socket.connect((self.robot_controller.ip, int(self.robot_controller.port)))
            get_logger(__name__).log(logging.INFO,
                                     f"Connection to robot socket established")
        except Exception as e:
            get_logger(__name__).log(logging.ERROR,
                                     f"Error in establishing connection to socket {e}")


    def handle_command(self, command, data):
        """
        This method receives the commands and relays the correct
        data to the robot

        Args:
            command (str)
            data (dict)
        """
        response = None
        get_logger(__name__).log(
            logging.INFO,
            f"Executing command {command} starting"
        )
        if command == CMD_HOME:
            self.robot_controller.move_home()          
        
        elif command == CMD_SOCKET_DET:
            if data["result"] == RES_SUCCESS:
                try:
                    unit = data["unit"]
                except KeyError:
                    raise Exception("'Unit' not in data")
                try:
                    coords = data["coords"]
                except KeyError:
                    raise Exception("'Coords' not in data")
            
                response = self.robot_controller.socket_detection(unit, coords)
            
            elif data["result"] == RES_FAIL or data["result"] == RES_UNRELIABLE:
                self.robot_controller.reposition_eoat(data)
        
        elif command == CMD_UNPLUG:
            self.robot_controller.plug_out()
        
        else:
            get_logger(__name__).log(
                logging.WARNING,
                f"Unknown robot command"
            )
        
        get_logger(__name__).log(
            logging.INFO,
            f"Executing {command} finished"
        )
        return response
    
    def handle_message(self, content, message):
        if content == MSG_CONTAINER_DOWN:
            #TODO: what to do when container is down?
            get_logger(__name__).log(
                logging.WARNING,
                f"{message}"
            )
        elif content == MSG_SAFETY:
            if "result" not in message:
                get_logger(__name__).log(
                    logging.WARNING,
                    f"Received message: {message}"
                )
            if message["result"] == RES_START or message["result"] == RES_END:
                get_logger(__name__).log(
                    logging.INFO,
                    "Received message: "+ message["message"]
                )
            elif message["result"] == RES_FOREIGN:
                get_logger(__name__).log(
                    logging.WARNING,
                    f"Received message: "+message["message"]
                )
                #Foreign object detected - stop the robot
                self.robot_controller.stop()
        else:
            get_logger(__name__).log(
                logging.WARNING,
                f"Received unknown message: {message}"
            )

    def send_message(self, message=str):
        response = None
        get_logger(__name__).log(logging.INFO,
            f"Sent command {message} to socket")
        self.robot_socket.sendall(message.encode())

        current_robot_pos = eval(self.robot_socket.recv(1024).decode())
        self.robot_controller.current_position = current_robot_pos[0]
        get_logger(__name__).log(logging.INFO,
                                 f"Received and updated new robot pos {self.robot_controller.current_position}")
        
        return response