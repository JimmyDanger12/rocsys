import math
from roc_logging import get_logger
import logging
from DRCF import *

MSG_SUCCESS = "successful socket detection"
MSG_NO_SUCCESS = "no/unreliable detection"
MSG_HOME = "home position"
COORD_RAD = 'm/rad'
COORD_DEG = 'mm/deg'
CAMERA_OS_X = -82
CAMERA_OS_Y = -6
CAMERA_OS_Z = 55.5

ACC_DET = False
AMOVE_ASYNC = True
#TODO global - adjust speeds for movements (incl. plug-in/-out)

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

def is_within(list1:list,list2:list,value:int):
    return all(abs((1-value) * x) <= abs(y) <= abs((1+value) * x) for x, y in zip(list2, list1))

class RobotController:
    """
    This class handles the commands directed at the robot.
    This includes calculations and translations.
    """

    def __init__(self, ip, port, home_position, front_socket_postion, speed):
        self.message_handler = None
        self.ip = ip
        self.port = port
        self.global_speed = speed
        self.home_positon = home_position
        self.fsp = front_socket_postion
        self.current_position = home_position
        self.initial_home = True
        self.safety_stop = False

    def reposition_eoat(self, data):
        """
        Repositions EOAT to another position to retake picture

        Args:
            data (_type_): _description_
        """
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
        
        if is_within(self.current_position,self.home_positon,0.0005):
            #if robot is at starting location: move close to the robot and retake image
            get_logger(__name__).log(logging.INFO,
                                     "first_movement")
            #camera offset
            coords[0] += CAMERA_OS_X
            coords[1] += CAMERA_OS_Y
            coords[2] += CAMERA_OS_Z
            #retake offset
            coords[0] += -250
            coords[2] += -100
            command = f"""amovel({coords},vel=300, acc=300, mod={DR_MV_MOD_REL})"""
            self._send_message(command)
            response = "retake image"

        elif self.safety_stop == False:
            get_logger(__name__).log(logging.INFO,
                                     "second_movement")
            #return response
            coords[0] += CAMERA_OS_X
            coords[1] += CAMERA_OS_Y
            coords[2] += CAMERA_OS_Z
            #safety offset
            coords[0] += -80
            if ACC_DET:
                mod = DR_MV_MOD_REL
            else:
                coords = self.fsp
                mod = DR_MV_MOD_ABS
            
            command = f"""movel({coords},vel=100, acc = 100, mod={mod})"""

            self._send_message(command)
            self.plug_in()

        return response
    
    def plug_in(self):
        #TODO: more precise
        amp = [-47,1.25,0,0,0,0]
        period = [10,0.25,0,0,0,0]
        wait_time = 10

        wave = True
        if wave:
            #first idea: move in a wave motion into the socket
            command = f"""amove_periodic({amp},period={period})"""
            self._send_message(command)
            command = f"""wait({wait_time})"""
            self._send_message(command)
            command = f"""stop({DR_SSTOP})"""
            self._send_message(command)
        else:
            #second idea: move with little stiffness (finds its own way)
            stiffness = [500,500,500,100,100,100] #default: [3000, 3000, 3000, 200, 200, 200]
            movement = [-47,0,0,0,0,0]
            command = f"""task_compliance_ctrl()"""
            self._send_message(command)
            command = f"""set_stiffnessx({stiffness})"""
            self._send_message(command)
            command = f"""movel({movement}, vel=75, acc=100, ref={DR_TOOL}, mod={DR_MV_MOD_REL})"""
            self._send_message(command)
            command = f"""release_compliance_ctrl()"""
            self._send_message(command)


    def move_home(self):
        """
        Moves the robot to the home position (set in config)
        """
        if self.initial_home:
            command = f"""move_home({DR_HOME_TARGET_USER})"""
        else:
            command = f"""amovel({self.home_positon},vel=300,acc=300,mod={DR_MV_MOD_ABS},ref={DR_BASE})"""
        self.safety_stop = False    

        self._send_message(command)

    def plug_out(self):
        """
        Starts the unplugging procedure
        """
        #TODO: more precise
        movement = [60,0,0,0,0,0]
        command = f"""movel({movement}, vel=50, acc=50, ref={DR_TOOL}, mod={DR_MV_MOD_REL})"""
        self._send_message(command)
        self.move_home()

    def stop(self):
        command = f"""stop({DR_SSTOP})"""
        self.safety_stop = True
        self._send_message(command)
        
    def collect_data(self):
        movement = [-1,0,0,0,0,0]
        self.message_handler.collect_data = True
        command = f"""movel({movement},vel=100,acc=100,ref={DR_TOOL},mod={DR_MV_MOD_REL})"""
        return self._send_message(command)
    
    def _send_message(self, command):
        message = str(command)
        return self.message_handler.send_message(message)