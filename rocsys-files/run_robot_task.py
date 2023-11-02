"""
This is the main script to be used for communication with the 
Flask Server which is responsible for robot movement.

Server github: 
"""
import sys
import socketio
import json
import time
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QGridLayout, QLabel
from commands import PlugInCommand, PlugOutCommand, CollectDataCommand

PLUG_IN_COMMAND = "plug-in"
PLUG_OUT_COMMAND = "plug-out"
COLLECT_DATA_COMMAND = "collect-data"
FLASK_URL = "http://192.168.137.2:4444"

class Status():
    Disconnected = "Disconnected"
    Connected = "Connected"
    PluggingIn = "Plugging In"
    Charging = "Charging"
    PluggingOut = "Plugging Out"
    Stopped = "Safety Stop"

sio = socketio.Client()

def send_message(output=dict):
    print(f"Sending message: {output}")
    sio.emit("message_output",json.dumps(output))

class SocketIOGUI(QWidget):
    def __init__(self,url):
        super().__init__()
        self.url = url
        self.status = Status.Disconnected
        self.initUI()
    
    def initUI(self):  
        self.setWindowTitle("RobotCommands GUI")
        self.setStyleSheet("background-color : skyblue;"
                            "background:QLinearGradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: 0 #87ceeb, stop: 1 #191970);")
        self.setFixedSize(1080, 920)
        
        self.status_label = QLabel(f"Status: {self.status}")
        self.status_label.setFixedSize(420,50)
        self.status_label.setStyleSheet("font:Bold;"
                                        "font-family:Helvetica;"
                                        "font-size:18px;"
                                        "background-color: white;"
                                        "color:darkred;"
                                        "border:1px solid black;")
        self.status_style = self.status_label.styleSheet()

        self.connect_button = QPushButton("Connect")
        self.connect_button.setFixedSize(420, 150)
        self.connect_button.setStyleSheet("background-color : lightgreen;"
                                            "font:Bold;" 
                                            "font-family:Helvetica;"
                                            "font-size:24px")
        self.connect_button.clicked.connect(self.connect_to_server)
        
        self.disconnect_button = QPushButton("Disconnect")
        self.disconnect_button.setFixedSize(420, 150)
        self.disconnect_button.setStyleSheet("background-color : red;"
                                            "font:Bold;" 
                                            "font-family:Helvetica;"
                                            "font-size:24px")
        self.disconnect_button.clicked.connect(self.disconnect_from_server)
        
        self.plug_in_button = QPushButton("Plug In Pose 1")
        self.plug_in_button.setFixedSize(420, 150)
        self.plug_in_button.setStyleSheet("background-color : darkturquoise;"
                                            "font:Bold;" 
                                            "font-family:Helvetica;"
                                            "font-size:24px")
        self.plug_in_button.clicked.connect(lambda state, x=0: self.plug_in(x))
        
        self.plug_in_button2 = QPushButton("Plug In Pose 2")
        self.plug_in_button2.setFixedSize(420, 150)
        self.plug_in_button2.setStyleSheet("background-color : darkturquoise;"
                                            "font:Bold;" 
                                            "font-family:Helvetica;"
                                            "font-size:24px")
        self.plug_in_button2.clicked.connect(lambda state, x=1: self.plug_in(x))
        
        self.plug_in_button3 = QPushButton("Plug In Pose 3")
        self.plug_in_button3.setFixedSize(420, 150)
        self.plug_in_button3.setStyleSheet("background-color : darkturquoise;"
                                            "font:Bold;" 
                                            "font-family:Helvetica;"
                                            "font-size:24px")
        self.plug_in_button3.clicked.connect(lambda state, x=2: self.plug_in(x))
        
        self.plug_in_button4 = QPushButton("Plug In Pose 4")
        self.plug_in_button4.setFixedSize(420, 150)
        self.plug_in_button4.setStyleSheet("background-color : darkturquoise;"
                                            "font:Bold;" 
                                            "font-family:Helvetica;"
                                            "font-size:24px")
        self.plug_in_button4.clicked.connect(lambda state, x=3: self.plug_in(x))
        
        self.plug_out_button = QPushButton("Plug Out")
        self.plug_out_button.setFixedSize(950, 150)
        self.plug_out_button.setStyleSheet("background-color : #AFEEEE;"
                                            "font:Bold;" 
                                            "font-family:Helvetica;"
                                            "font-size:24px")
        self.plug_out_button.clicked.connect(self.plug_out)
        
        layout = QGridLayout(self)
        layout.addWidget(self.status_label, 0, 0, 1, 2)
        layout.addWidget(self.connect_button, 1, 0)
        layout.addWidget(self.disconnect_button, 1, 1)
        layout.addWidget(self.plug_in_button, 2, 0)
        layout.addWidget(self.plug_in_button2, 2, 1)
        layout.addWidget(self.plug_in_button3, 3, 0)
        layout.addWidget(self.plug_in_button4, 3, 1)
        layout.addWidget(self.plug_out_button, 4, 0, 1, 2)
        
        self.setLayout(layout)
    
    def update_status(self,status=Status):
        self.status = status
        self.status_label.setText(f"Status: {self.status}")

        if self.status == Status.Disconnected:
            modified_style_sheet = f"{self.status_style} color:darkred;"
        elif self.status == Status.Connected:
            modified_style_sheet = f"{self.status_style} color:darkgreen;"
        elif status == Status.PluggingIn or status == Status.PluggingOut:
            modified_style_sheet = f"{self.status_style} color:orange;"
        elif status == Status.Charging:
            modified_style_sheet = f"{self.status_style} color:darkblue;"
        elif status == Status.Stopped:
            modified_style_sheet = f"{self.status_style} background-color:darkred;color:white;"
        
        self.status_label.setStyleSheet(modified_style_sheet)
        
    def connect_to_server(self):
        sio.connect(self.url)
        self.update_status(Status.Connected)
    
    def disconnect_from_server(self):
        sio.disconnect()
        self.update_status(Status.Disconnected)
    
    def plug_in(self,target):
        if self.status == Status.Connected or self.status == Status.Stopped:
            self.cmd = PlugInCommand(self.url,target,sio)
            self.execute_command(self.cmd)
            self.update_status(Status.PluggingIn)
    
    def plug_out(self):
        if self.status == Status.Charging or self.status == Status.Connected or self.status == Status.Stopped:
            cmd = PlugOutCommand(self.url)
            self.execute_command(cmd)
            self.update_status(Status.PluggingOut)
    
    def collect_data(self):
        self.execute_command(CollectDataCommand(self.url))
    
    def execute_command(self,command):
        try:
            print(f"Execution of {command.__class__.__name__} started!")
            message = command.execute()
            send_message(message)
            print(f"Execution of {command.__class__.__name__} finished!")
        except Exception as e:
            print("Exception",e)

def on_connect():
    print("Connected to server")

def on_disconnect():
    print("Disconnect from server")
    app.quit()

def on_message(message):
    print(print(f"Received message from server: {message}"))
    if message == "plug_in_complete":
        gui.update_status(Status.Charging)
    if message == "plug_out_complete":
        time.sleep(9) #to allow for async movement to complete
        gui.update_status(Status.Connected)
    if message == "safety_stop_response" and (gui.status == Status.PluggingIn or gui.status == Status.PluggingOut):
        gui.update_status(Status.Stopped)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    gui = SocketIOGUI(FLASK_URL)
    gui.show()
    
    sio.on("connect",on_connect)
    sio.on("disconnect",on_disconnect)
    sio.on("message_input",on_message)
    sio.on("message_all",on_message)
    sys.exit(app.exec_())