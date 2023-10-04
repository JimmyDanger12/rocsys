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

class RobotController():
    """
    This class handles the commands directed at the robot.
    This includes calculations and translations.
    """

    def __init__(self, home_position, speed):
        self.home_position = home_position
        self.current_position = home_position
        self.global_speed = speed

    def reposition_eoat(self, data):
        """
        Repositions EOAT to another position to retake picture

        Args:
            data (_type_): _description_
        """
        #TODO:
        pass

    def move_to_coords(self, unit, coords):
        """
        Moves the robot to the coordinates

        Args:
            unit (str): 'm/rad','mm/deg'
            coords (list): [x,y,z,rx,ry,rz]
        """
        coords = convert_coords(unit, coords)
        if all([x == 0 for x in coords]):
            get_logger(__name__).log(
                logging.ERROR,
                f"No/empty coordinates provided"
            )
            raise
        
        return
        #TODO
        movej(coords)

    def move_home(self):
        """
        Moves the robot to the home position (set in config)
        """
        #TODO:
        return
        movej(self.home_position)
        self.current_position = get_current_posx() #implement

    def unplug(self):
        """
        Starts the unplugging procedure
        """
        #TODO:
        return
        #move in x-direction out of socket (for certain distance)
        movej(self.home_position)
        self.current_position = get_current_posx()