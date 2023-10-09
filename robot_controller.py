import math
from roc_logging import get_logger
import logging
from DRCF import *

MSG_SUCCESS = "successful socket detection"
MSG_NO_SUCCESS = "no/unreliable detection"
MSG_HOME = "home position"
COORD_RAD = 'm/rad'
COORD_DEG = 'mm/deg'

def convert_coords(unit, coords):
    """
    converts coordinates from m/rad to mm/deg

    Args:
        unit (str): _description_
        coords (list): _description_

    Returns:
        coords (list): [x,y,z,rx,ry,rz] 
    """
    converted_coords = list()
    if unit == COORD_RAD:
        converted_coords[0:2] = [x*1000 for x in coords[0:3]]
        converted_coords[3:5] = [math.degrees(rad) for rad in coords[3:6]]
    if unit == COORD_DEG:
        converted_coords = coords
    return converted_coords

class RobotController:
    """
    This class handles the commands directed at the robot.
    This includes calculations and translations.
    """

    def __init__(self, ip, port, home_position, speed):
        self.message_handler = None
        self.ip = ip
        self.port = port
        self.global_speed = speed
        self.home_positon = home_position
        self.current_position = home_position

    def reposition_eoat(self, data):
        """
        Repositions EOAT to another position to retake picture

        Args:
            data (_type_): _description_
        """
        #TODO: implement (optional)
        pass

    def socket_detection(self, unit, coords):
        """
        Moves the robot to the coordinates

        Args:
            unit (str): 'm/rad','mm/deg'
            coords (list): [x,y,z,rx,ry,rz]
        """
        response = None
        coords = convert_coords(unit, coords)
        if all([x == 0 for x in coords]):
            get_logger(__name__).log(
                logging.ERROR,
                f"No/empty coordinates provided"
            )
            raise
        
        if self.current_position == self.home_positon:
            #if robot is at starting location: move close to the robot and retake image
            #TODO: implement offset
            coords[0] -= 200
            command = f"""movel({coords},vel=100, acc=100, mod={DR_MV_MOD_REL})"""
            self._send_message(command)
            wait(10) #wait for robot movement to finish #TODO:
            response = "retake image"
        else:
            coords[0] -= 200
            command = f"""movel({coords},vel=100, acc = 100, mod={DR_MV_MOD_REL})"""
            self._send_message(command)
            #self.plug_in()

        return response
    
    def plug_in(self):
        #TODO: more precise
        amp = [-50,5,0,0,0,0]
        period = [4,0.5,0,0,0,0]
        wait_time = 2
        command = f"""
            amove_periodic({amp},
                    period={period})
            wait({wait_time})
            stop(DR_SSTOP)
            """
        self._send_message(command)


    def move_home(self):
        """
        Moves the robot to the home position (set in config)
        """
        command = f"""move_home({DR_HOME_TARGET_USER})"""

        self._send_message(command)

    def plug_out(self):
        """
        Starts the unplugging procedure
        """
        #TODO: wiggle?
        movement = [50,0,0,0,0,0]
        command = f"""
            movel({movement}, ref={DR_TOOL}, mod={DR_MV_MOD_REL})
            move_home({DR_HOME_TARGET_USER})
            """
        self._send_message(command)
        

    
    def _send_message(self, command):
        message = str(command)
        self.message_handler.send_message(message)