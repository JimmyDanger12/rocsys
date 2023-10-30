import subprocess
import requests
import socketio
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout
import json
import time
import csv
import math

DOCKER_COMMAND = "docker exec -it vision-vision-1 bash -c 'rocsys-vision-client DETECT_SOCKET_FAST'"
SLEEP_TIME = 12 #no delay needed - as robot only sends complete signal when movement is done

MST_CMD = "cmd"
MST_MSG = "msg"

CT_SOCKET_DET = "socket_detection"
CT_RESET_PLUG_IN = "reset_plug_in"
CT_PLUG_IN = "start_plug_in"
CT_UNPLUG = "start_unplug"
CT_UNKOWN = "unkown_response"
CT_COLLECT_DATA = "collect_data"

FIELD_MESSAGE_TYPE = "message_type"
FIELD_CONTENT = "content"
FIELD_DATA = "data"
FIELD_MESSAGE = "message"
FIELD_ERROR = "error"
FIELD_RESPONSE = "response"

RES_NO_SUCCESS = 0
RES_SUCCESS = 1
RES_UNRELIABLE = 2

MSG_TAKE = "take image"
MSG_RETAKE = "retake image"
MSG_IN_POSITION = "in position"

def extract_coords(text=str):
    coords_str = text.split('Pose: ')[1].split('\n')[0]
    coords = eval(coords_str)
    return coords

def convert_coords(coords):
    converted_coords = list()
    converted_coords[0:2] = [x*1000 for x in coords[0:3]]
    converted_coords[3:5] = [math.degrees(rad) for rad in coords[3:6]]
    return converted_coords

class PlugInCommand():
    def __init__(self, url, target,sio):
        self.flask_url = url
        self.initial_home = True
        self.target = target
        self.sio = sio
        
        sio.on("take_image",self.handle_response)
    
    def handle_response(self,msg):
        print(msg)
        if msg == MSG_TAKE:
            self.send_message(self.take_image())
        elif msg == MSG_RETAKE:
            time.sleep(SLEEP_TIME)
            self.send_message(self.take_image())
        elif msg == MSG_IN_POSITION:
            time.sleep(SLEEP_TIME*1.5)
            self.send_message(self.plug_in())
        
    def execute(self):
        #first move to home position
        return self.reset_plug_in(self.target)
        
    def send_message(self,output=dict):
        print(f"Sending message: {output}")
        self.sio.emit("message_output",json.dumps(output))
    
    def reset_plug_in(self,target):
        print(target)
        message_type = MST_CMD
        content = CT_RESET_PLUG_IN
        data = {"target":target}
        
        output = {
            FIELD_MESSAGE_TYPE: message_type,
            FIELD_CONTENT: content,
            FIELD_DATA: str(data)
        }
        
        return output
    
    def take_image(self):
        try:
            docker_output = subprocess.check_output(DOCKER_COMMAND, shell=True, text=True, stderr=subprocess.STDOUT).strip()
        except subprocess.CalledProcessError as e:
            docker_output = e.output

        message_type = MST_MSG
        content = None
        data = {}

        if "not running" in docker_output:
            print(docker_output)
            content = "container_down"
        else:
            print("Container up and running!")

        if "success" in docker_output:
            message_type = MST_CMD
            content = CT_SOCKET_DET
            
            result = RES_SUCCESS
            unit = "m/rad"
            coords = extract_coords(docker_output)
            data = {
                "result": result,
                "unit": unit,
                "coords": coords
            }
        elif "No socket detected" in docker_output or "unreliable" in docker_output:
            message_type = MST_CMD
            content = CT_SOCKET_DET
            result = RES_NO_SUCCESS if "No socket detected" in docker_output else RES_UNRELIABLE
            data = {
                "result": result
            }
        elif content:
            data = {
                "message": docker_output
            }
        else:
            content = CT_UNKOWN
            data = {
                "message": docker_output
            }


        output = {
            FIELD_MESSAGE_TYPE: message_type,
            FIELD_CONTENT: content,
            FIELD_DATA: data
        }
        
        return output
    
    def plug_in(self):
        message_type = MST_CMD
        content = CT_PLUG_IN
        data = {}
        
        output = {
            FIELD_MESSAGE_TYPE: message_type,
            FIELD_CONTENT: content,
            FIELD_DATA: data
        }
        return output
    
class PlugOutCommand():
    def __init__(self, url):
        self.flask_url = url
    
    def execute(self):
        message_type = MST_CMD
        content = CT_UNPLUG
        data = {}
        
        output = {
            FIELD_MESSAGE_TYPE: message_type,
            FIELD_CONTENT: content,
            FIELD_DATA: data
        }
        
        return output

class CollectDataCommand():
    def __init__(self, url):
        self.flask_url = url
        self.amount = 150
        self.file_path = "coord.csv"
    
    def execute(self):
        message_type = MST_CMD
        content = CT_COLLECT_DATA
        data = {}
        
        output = {
            FIELD_MESSAGE_TYPE: message_type,
            FIELD_CONTENT: content,
            FIELD_DATA: data
        }
        for i in range(self.amount):
            response = send_message(self.flask_url, output)
            robot_coords = response["response"]
        
            results, coord_list = self.take_image(self.amount)
            image_coords = convert_coords(coord_list[0])
            
            with open(self.file_path, mode="a", newline="") as file:
                writer = csv.writer(file)
                total_coords=robot_coords+image_coords
                writer.writerow(total_coords)
        
        return response
        
    
    def take_image(self, amount):
        results = list()
        coords_list = list()
        for i in range(1):
            try:
                docker_output = subprocess.check_output(DOCKER_COMMAND, shell=True, text=True, stderr=subprocess.STDOUT).strip()
            except subprocess.CalledProcessError as e:
                docker_output = e.output

            if "not running" in docker_output:
                print(docker_output)
            else:
                print("image taken")
            result = None
            
            if "success" in docker_output:        
                result = RES_SUCCESS
                coords = extract_coords(docker_output)
                coords_list.append(coords)
            elif "No socket detected" in docker_output or "unreliable" in docker_output:
                result = RES_NO_SUCCESS if "No socket detected" in docker_output else RES_UNRELIABLE
                coords = []
            
            results.append(result)
        return results, coords_list
