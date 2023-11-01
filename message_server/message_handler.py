import logging
import socket
from message_server.robot_controller import RobotController
from message_server.roc_logging import get_logger

CMD_RESET_PLUG_IN = "reset_plug_in"
CMD_SOCKET_DET = "socket_detection"
CMD_PLUG_IN = "start_plug_in"
CMD_UNPLUG = "start_unplug"
CMD_COLLECT_DATA = "collect_data"
MSG_SAFETY = "safety_detection"
MSG_CONTAINER_DOWN = "container_down"

RES_FAIL = 0
RES_SUCCESS = 1
RES_UNRELIABLE = 2

RES_START = 1
RES_END = 2
RES_FOREIGN = 0

TGT_ROBOT = "message_robot"
TGT_INPUT = "message_input"
TGT_SAFETY = "message_safety"
TGT_TAKE_IMAGE = "take_image"

FIELD_TARGET = "target"
FIELD_UNIT = "unit"
FIELD_COORDS = "coords"
FIELD_RESULT = "result"
FIELD_MESSAGE = "message"

class MessageHandler():
    """
    This class handles the management of the robot commands 
    and relays them to the robot

    """

    def __init__(self, server, robot_controller:RobotController):
        self.server = server
        self.robot_controller = robot_controller
        self.robot_controller.message_handler = self
        self.collect_data = False
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
        This method receives the commands and executes the correct 
        correspondent robot command

        Args:
            command (str)
            data (dict)
        """

        if command == CMD_RESET_PLUG_IN or command == CMD_UNPLUG or not self.robot_controller.safety_stop:
            get_logger(__name__).log(
            logging.INFO,
            f"Executing command {command} starting"
            )
            if command == CMD_RESET_PLUG_IN:
                self.robot_controller.move_home(False) 
                if FIELD_TARGET in data:
                    target = eval(data)[FIELD_TARGET]
                    self.robot_controller.front_socket_position = self.robot_controller.fsp_list[target]
                self.send_message(TGT_SAFETY,"start_detection")
                self.send_message(TGT_TAKE_IMAGE,"take image")
            elif command == CMD_SOCKET_DET:
                if data[FIELD_RESULT] == RES_SUCCESS:
                    try:
                        unit = data[FIELD_UNIT]
                    except KeyError:
                        raise Exception("'Unit' not in data")
                    try:
                        coords = data[FIELD_COORDS]
                    except KeyError:
                        raise Exception("'Coords' not in data")
                    self.robot_controller.socket_detection(unit, coords)
                
                elif data[FIELD_RESULT] == RES_FAIL or data[FIELD_RESULT] == RES_UNRELIABLE:
                    self.robot_controller.reposition_eoat(data)
            
            elif command == CMD_PLUG_IN:
                self.robot_controller.plug_in()
            
            elif command == CMD_UNPLUG:
                self.robot_controller.plug_out()

            elif command == CMD_COLLECT_DATA: #optional command
                self.robot_controller.collect_data()
            
            else:
                get_logger(__name__).log(
                    logging.WARNING,
                    f"Unknown robot command"
                )
            
            get_logger(__name__).log(
                logging.INFO,
                f"Executing command {command} finished"
            )
        else:
            get_logger(__name__).log(
                logging.WARNING,
                f"No execution of command {command} due to safety stop"
            )
    
    def handle_message(self, content, message):
        """
        Handle messages that are not inherently a command and log them,
        also includes the safety stop

        Args:
            content (str):
            message (dict)
        """
        if content == MSG_CONTAINER_DOWN:
            get_logger(__name__).log(
                logging.WARNING,
                f"{message}"
            )
        elif content == MSG_SAFETY:
            if FIELD_RESULT not in message:
                get_logger(__name__).log(
                    logging.WARNING,
                    f"Unknown result from safety-system: {message}"
                )
            if message[FIELD_RESULT] == RES_START or message[FIELD_RESULT] == RES_END:
                get_logger(__name__).log(
                    logging.INFO,
                    "Safety-system: "+ message[FIELD_MESSAGE]
                )
                self.send_message(TGT_SAFETY,"safety_start_received")
            elif message["result"] == RES_FOREIGN:
                get_logger(__name__).log(
                    logging.WARNING,
                    f"Safety-system: "+message[FIELD_MESSAGE]
                )
                #Foreign object detected - stop the robot
                self.robot_controller.stop()
        else:
            get_logger(__name__).log(
                logging.WARNING,
                f"Received unknown message: {message}"
            )

    def send_message(self, target:str,message:str):
        """
        This function sends messages to the robot - and saves the returned robot information.
        This includes most importantly the current robot location, but also force information

        If the message is not addressed to the robot socket - execute the server's message function

        Args:
            target (str): _description_
            message (str): _description_
        """
        if target == TGT_ROBOT:
            get_logger(__name__).log(logging.INFO,
                f"Sent command {message} to robot socket")
            self.robot_socket.sendall(message.encode())

            #robot_information receives the returned information about the robot (most importantly the current positon)
            robot_information = eval(self.robot_socket.recv(1024).decode())
            current_robot_pos = eval(robot_information["current_pos"])[0]
            joint_torque = robot_information["joint_torque"]
            ext_torque = robot_information["external_torque"]
            tool_force = robot_information["tool_force"]

            self.robot_controller.current_position = current_robot_pos
            if "move_home" in message: #when moving to actual robot-home position(without async), set actual home pos as program home pos
                self.robot_controller.home_position = current_robot_pos
                get_logger(__name__).log(logging.INFO,
                                        f"Received and updated new robot home pos {self.robot_controller.home_position}")
            
            if self.collect_data:
                self.server.send_message(TGT_INPUT,current_robot_pos)
            get_logger(__name__).log(logging.INFO,
                                    f"Received and updated current robot pos {self.robot_controller.current_position}")
        else:
            self.server.send_message(target,message)