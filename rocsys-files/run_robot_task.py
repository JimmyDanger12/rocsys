"""
This is the main script to be used for communication with the 
Flask Server which is responsible for robot movement.

Server github: 
"""
import sys
import socketio
import json
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QGridLayout
from commands import PlugInCommand, PlugOutCommand, CollectDataCommand

PLUG_IN_COMMAND = "plug-in"
PLUG_OUT_COMMAND = "plug-out"
COLLECT_DATA_COMMAND = "collect-data"
FLASK_URL = "http://192.168.137.2:4444"

sio = socketio.Client()
status = None

def send_message(output=dict):
    print(f"Sending message: {output}")
    sio.emit("message_output",json.dumps(output))

class SocketIOGUI(QWidget):
    def __init__(self,url):
        super().__init__()
        self.url = url
        self.initUI()
    
    def initUI(self):  
        self.setWindowTitle("RobotCommands GUI")
        self.setStyleSheet("background-color : skyblue;"
                            "background:QLinearGradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: 0 #87ceeb, stop: 1 #191970);")
        self.setFixedSize(760, 560)
        
        self.connect_button = QPushButton("Connect")
        self.connect_button.setFixedSize(350, 150)
        self.connect_button.setStyleSheet("background-color : lightgreen;"
                                            "font:Bold;" 
                                            "font-family:Helvetica;"
                                            "font-size:18px")
        self.connect_button.clicked.connect(self.connect_to_server)
        
        self.disconnect_button = QPushButton("Disconnect")
        self.disconnect_button.setFixedSize(350, 150)
        self.disconnect_button.setStyleSheet("background-color : red;"
                                            "font:Bold;" 
                                            "font-family:Helvetica;"
                                            "font-size:18px")
        self.disconnect_button.clicked.connect(self.disconnect_from_server)
        
        """self.plug_in_button = QPushButton("Plug In Pose 1")
        self.plug_in_button.setFixedSize(350, 150)
        self.plug_in_button.setStyleSheet("background-color : darkturquoise;"
                                            "font:Bold;" 
                                            "font-family:Helvetica;"
                                            "font-size:18px")
        self.plug_in_button.clicked.connect(self.plug_in_0)"""
        
        self.plug_in_button2 = QPushButton("Plug In")
        self.plug_in_button2.setFixedSize(720, 150)
        self.plug_in_button2.setStyleSheet("background-color : darkturquoise;"
                                            "font:Bold;" 
                                            "font-family:Helvetica;"
                                            "font-size:18px")
        self.plug_in_button2.clicked.connect(self.plug_in_0)
        
        self.plug_out_button = QPushButton("Plug Out")
        self.plug_out_button.setFixedSize(720, 150)
        self.plug_out_button.setStyleSheet("background-color : darkturquoise;"
                                            "font:Bold;" 
                                            "font-family:Helvetica;"
                                            "font-size:18px")
        self.plug_out_button.clicked.connect(self.plug_out)
        
        layout = QGridLayout(self)
        layout.addWidget(self.connect_button, 0, 0)
        layout.addWidget(self.disconnect_button, 0, 1)
        #layout.addWidget(self.plug_in_button, 1, 0)
        layout.addWidget(self.plug_in_button2, 1, 0, 1, 2)
        layout.addWidget(self.plug_out_button, 2, 0, 1, 2)
        
        self.setLayout(layout)
        
    def connect_to_server(self):
        sio.connect(self.url)
    
    def disconnect_from_server(self):
        sio.disconnect()
    
    def plug_in_0(self):
        target = 0
        self.plug_in(target)
    
    def plug_in_1(self):
        target=1
        self.plug_in(target)
    
    def plug_in(self,target):
        self.cmd = PlugInCommand(self.url,target,sio)
        self.execute_command(self.cmd)
    
    def plug_out(self):
        cmd = PlugOutCommand(self.url)
        self.execute_command(cmd)
    
    def collect_data(self):
        self.execute_command(CollectDataCommand(self.url))
    
    def execute_command(self,command):
        try:
            print(f"Execution of {command}-command started!")
            message = command.execute()
            send_message(message)
            print(f"Execution of {command}-command finished!")
        except Exception as e:
            print(e)

def on_connect():
    print("Connected to server")

def on_disconnect():
    print("Disconnect from server")
    app.quit()

def on_message(message):
    print(message)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    gui = SocketIOGUI(FLASK_URL)
    gui.show()
    
    sio.on("connect",on_connect)
    sio.on("disconnect",on_disconnect)
    sio.on("message_input",on_message)
    sio.on("message_all",on_message)
    sys.exit(app.exec_())