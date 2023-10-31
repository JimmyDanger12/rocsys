import math
import numpy as np
from message_server.roc_logging import get_logger
import logging

# if Doosan Robot Control Functions import does not work: read global below variables
from DRCF import *
"""
DR_MV_MOD_ABS = 0
DR_MV_MOD_REL = 1
DR_TOOL = 1
DR_SSTOP = 2
DR_HOME_TARGET_USER = 1
"""

MSG_SUCCESS = "successful socket detection"
MSG_NO_SUCCESS = "no/unreliable detection"
MSG_HOME = "home position"
COORD_RAD = 'm/rad'
COORD_DEG = 'mm/deg'
CAMERA_OS_X = -82
CAMERA_OS_Y = -6
CAMERA_OS_Z = 55.5
TGT_ROBOT = "message_robot"
TGT_INPUT = "message_input"
TGT_SAFETY = "message_safety"
TGT_ALL = "message_all"
TGT_TAKE_IMAGE = "take_image"

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

def apply_camera_offset(coords:list,camera_os:list):
    """
    apply camera offset to coordinates,
    offset is set in config

    Args:
        coords (list): original coords
        camera_os (list): camera offset

    Returns:
        list: updated coords
    """
    coords = list(np.array(coords)+np.array(camera_os))
    return coords

def is_within(list1:list,list2:list,value:int):
    """_summary_

    Args:
        list1 (list): first list
        list2 (list): second list
        value (int): limit

    Returns:
        bool: True if all values are within the limit
    """
    return all(abs((1-value) * x) <= abs(y) <= abs((1+value) * x) for x, y in zip(list2, list1))

class RobotController:
    """
    This class handles the commands directed at the robot.
    This includes calculations and translations.
    """

    def __init__(self, ip, port, home_position, camera_os, accurate_detection):
        #server/messaging vars
        self.message_handler = None
        self.ip = ip
        self.port = port

        #robot vars
        self.camera_os = camera_os
        self.home_position = home_position
        self.current_position = home_position
        self.front_socket_position = None

        #vars for various purposes
        self.initial_home = True
        self.safety_stop = False
        
        #vars for not accurate detection
        self.accurate_detection = accurate_detection
        self.fsp_list = None

    def socket_detection(self, unit, coords):
        """
        Socket detection logic:
        - take image:
         - move to coordinates which are close to detection (for closer/better second detection)
        - take second image:
         - move directly to detection (if accurate detection)
         - move to specified coords depending on provided (hard-coded) fsp

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
        
        if is_within(self.current_position,self.home_position,0.01):
            #if robot is at starting location: move close to the robot and retake image
            get_logger(__name__).log(logging.INFO,
                                     "Executing first detection movement command")
            
            #camera offset
            coords = apply_camera_offset(coords,self.camera_os)
            #retake offset
            coords[0] += -320
            coords[2] += -70
            coords[4] = coords[4]/2
            command = f"""amovel({coords},vel=300, acc=300, mod={DR_MV_MOD_REL})"""
            self._send_message(TGT_ROBOT,command)
            self._send_message(TGT_TAKE_IMAGE,"retake image")

        else:
            get_logger(__name__).log(logging.INFO,
                                     "Executing second detection movement command")
            
            coords = apply_camera_offset(coords,self.camera_os)
            #coords[0] += -80 #safety offset TODO: remove
            mod = DR_MV_MOD_REL

            if not self.accurate_detection and self.fsp_list: #only when socket detection is not accurate enough
                mod = DR_MV_MOD_ABS
                coords = self.front_socket_position
                
                get_logger(__name__).log(
                        logging.INFO,
                        f"Targeting fsp {coords}"
                    )
            
            command = f"""amovel({coords},vel=100, acc = 100, mod={mod})"""
            self._send_message(TGT_ROBOT,command)
            self._send_message(TGT_TAKE_IMAGE,"in position")
    
    def plug_in(self):
        """
        This command initiates the plugging-in of the plug into the socket
        Options for force control or 'wiggle' are available
        """
        #TODO: force control?
        amp = [-50,1.25,0,0,0,0]
        period = [10,0.25,0,0,0,0]
        wait_time = 10

        wave = True
        if wave:
            #first idea: move in a wave motion into the socket
            command = f"""amove_periodic({amp},period={period})"""
            self._send_message(TGT_ROBOT,command)
            command = f"""wait({wait_time})"""
            self._send_message(TGT_ROBOT,command)
            command = f"""stop({DR_SSTOP})"""
            self._send_message(TGT_ROBOT,command)
        else:
            #second idea: move with little stiffness (finds its own way)
            stiffness = [3000,6000,20000,5000,5000,5000] #default: [3000, 3000, 3000, 200, 200, 200]
            movement = [-49,0,0,0,0,0]
            command = f"""task_compliance_ctrl({stiffness})"""
            self._send_message(TGT_ROBOT,command)
            command = f"""movel({movement}, vel=75, acc=100, ref={DR_TOOL}, mod={DR_MV_MOD_REL})"""
            self._send_message(TGT_ROBOT,command)
            command = f"""release_compliance_ctrl()"""
            self._send_message(TGT_ROBOT,command)
        self._send_message(TGT_INPUT,"plug_in_complete")

    def move_home(self,interrupt=False):
        """
        Moves the robot to the home position (set in config)
        """
        if not interrupt:
            command = f"""move_home({DR_HOME_TARGET_USER})"""
        else:
            command = f"""amovel({self.home_position},vel=300,acc=300)"""
        self.safety_stop = False    

        self._send_message(TGT_ROBOT,command)

    def plug_out(self):
        """
        Starts the unplugging procedure:
        move 6 cm in the x-direction from the tools perspective
        """
        movement = [60,0,0,0,0,0]
        command = f"""movel({movement}, vel=50, acc=50, ref={DR_TOOL}, mod={DR_MV_MOD_REL})"""
        self._send_message(TGT_ROBOT,command)
        self.move_home(True)
        self._send_message(TGT_INPUT,"plug_out_complete")

    def stop(self):
        """
        Send soft stop command to robot (safety interrupt) to 
        interrupt current movement command
        """
        command = f"""stop({DR_SSTOP})"""
        self.safety_stop = True
        self._send_message(TGT_ROBOT,command)
        self._send_message(TGT_ALL,"safety_stop_response")
        
    def collect_data(self):
        """
        currently: data will be safed on RL - rewrite if saved on OL
        """
        movement = [-1,0,0,0,0,0]
        self.message_handler.collect_data = True
        command = f"""movel({movement},vel=100,acc=100,ref={DR_TOOL},mod={DR_MV_MOD_REL})"""
        self._send_message(TGT_ROBOT,command)
    
    def reposition_eoat(self, data): #not implemented
        """
        Repositions EOAT to another position to retake picture

        Args:
            data (_type_): _description_
        """
        pass
    
    def _send_message(self, target,command):
        """
        Relegates message to message handler
        """
        message = str(command)
        return self.message_handler.send_message(target,message)