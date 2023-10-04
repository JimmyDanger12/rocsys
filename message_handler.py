import logging
from robot import RobotController
from roc_logging import get_logger

CMD_HOME = "move_home"
CMD_SOCKET_DET = "socket_detection"
CMD_UNPLUG = "start_unplug"
MSG_CONTAINER_DOWN = "container_down"
MSG_UNKNOWN_RESPONSE = "unknown_response"

RES_FAIL = 0
RES_SUCCESS = 1
RES_UNRELIABLE = 2

class MessageHandler():
    """
    This class handles the management of the robot commands 
    and relays them to the robot

    """

    def __init__(self, server, robot_controller:RobotController):
        self.server = server
        self.robot_controller = robot_controller

    def handle_command(self, command, data):
        """
        This method receives the commands and relays the correct
        data to the robot

        Args:
            command (str)
            data (dict)
        """
        get_logger(__name__).log(
            logging.INFO,
            f"Executing command {command} starting"
        )
        if command == CMD_HOME:
            self.robot_controller.move_home()          
        
        elif command == CMD_SOCKET_DET:
            if data["result"] == RES_SUCCESS:

                #TODO: implement home/quadrant differentiation
                try:
                    unit = data["unit"]
                except KeyError:
                    raise Exception("'Unit' not in data")
                try:
                    coords = data["coords"]
                except KeyError:
                    raise Exception("'Coords' not in data")
            
                self.robot_controller.move_to_coords(unit, coords)
            
            elif data["result"] == RES_FAIL or data["result"] == RES_UNRELIABLE:
                self.robot_controller.reposition_eoat(data)
        
        elif command == CMD_UNPLUG:
            self.robot_controller.unplug()
        
        else:
            get_logger(__name__).log(
                logging.WARNING,
                f"Unknown robot command"
            )
        
        get_logger(__name__).log(
            logging.INFO,
            f"Executing {command} finished"
        )
    
    def handle_message(self, content, message):
        if content == "container_down":
            #TODO: what to do when container is down?
            get_logger(__name__).log(
                logging.WARNING,
                f"{message}"
            )
        else:
            get_logger(__name__).log(
                logging.WARNING,
                f"Received unknown message: {message}"
            )