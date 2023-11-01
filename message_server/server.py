from flask import Flask, request
from flask_socketio import SocketIO
import logging
from message_server.globalconfig import GlobalConfig
from message_server.roc_logging import setup_logging, get_logger
from message_server.robot_controller import RobotController
from message_server.message_handler import MessageHandler

FIELD_MESSAGE_TYPE = "message_type"
FIELD_CONTENT = "content"
FIELD_DATA = "data"
FIELD_ERROR = "error"
FIELD_ROBOT = "ROBOT"
FIELD_CAMERA = "CAMERA"
FIELD_SERVERCONFIG = "SERVERCONFIG"
CMD = "cmd"
MSG = "msg"
TGT_ALL = "message_all"

class Server():
    """
    This class implements a Flask server used to send/receive
    messages from the rocsys python script and starts the message and command handling.    
    """

    def __init__(self):
        self.server = None
        self.socketio = None
        self.robot_controller = None
        self.message_handler = None

    def start(self, config: GlobalConfig):
        """
        This method sets up the Flask server using the 
        config settings set in GlobalConfig (default: config.ini)


        Args:
            config (GlobalConfig)
        """

        setup_logging(config)
        get_logger(__name__).log(
            100,
            f"Flask server starting..."
        )
        
        self.server = Flask(__name__)
        self.socketio = SocketIO(self.server)

        host = config[FIELD_SERVERCONFIG, "host"]
        port = config[FIELD_SERVERCONFIG, "port"]
        debug = eval(config[FIELD_SERVERCONFIG, "debug"])

        robot_ip = config[FIELD_ROBOT, "ip"]
        robot_port = config[FIELD_ROBOT, "port"]
        home_position = eval(config[FIELD_ROBOT, "home_position"])
        detection_acc = eval(config[FIELD_ROBOT, "accurate_detection"])
        plug_in_method = eval(config[FIELD_ROBOT,"plug_in_method"])

        camera_os = eval(config[FIELD_CAMERA,"os"])

        self.robot_controller = RobotController(robot_ip, robot_port, home_position, camera_os, detection_acc, plug_in_method)
        self.message_handler = MessageHandler(self, self.robot_controller)

        if detection_acc == False: #only used if rocsys-client detections are inaccurate -> use hard-coded positions
            robot_fsps = eval(config[FIELD_ROBOT,"front_socket_positions"])
            self.robot_controller.fsp_list = robot_fsps
        
        @self.socketio.on("message_output")
        def receive_message(message):
            """
            This is the default route for the Flask server 
            to listen to messages from the docker output

            Returns:
                returns a message to original sender
            """
            message_raw = eval(message)
            try:
                self.handle_message(message_raw)
            except Exception as e:
                get_logger(__name__).error(e)
                self.send_message(TGT_ALL,{FIELD_ERROR:str(e)})
        
        @self.socketio.on("connect")
        def handle_connect():
            client_ip = request.environ["REMOTE_ADDR"]
            get_logger(__name__).log(logging.INFO,
                                     f"Client connected from IP: {client_ip}")
        
        @self.socketio.on("disconnect")
        def handle_disconnect():
            client_ip = request.environ["REMOTE_ADDR"]
            get_logger(__name__).log(logging.INFO,
                                     f"Client disconnected from IP: {client_ip}")
        
        try:
            self.socketio.run(self.server, host=host, port=port, debug=debug)
            
        except Exception as e:
            get_logger(__name__).error(e)
            raise
        finally:
            self.message_handler.robot_socket.close()
            get_logger(__name__).log(
                100,
                f"Flask server shutting down"
            )

    def handle_message(self, message):
        """
        This method handles the incoming messages and relays
        them to the relating handler.

        Args:
            message (str): {
                message_type (str): ('cmd', 'msg'),
                content (str): ('socket_det'),
                data (dict)
            }
        """
        missing_keys = {FIELD_MESSAGE_TYPE, FIELD_CONTENT, FIELD_DATA}.difference(message.keys())
        
        if missing_keys:
            raise Exception(f"Message is missing key(s): {missing_keys}")

        message_type = message[FIELD_MESSAGE_TYPE]
        content = message[FIELD_CONTENT]
        data = message[FIELD_DATA]

        get_logger(__name__).log(
            logging.INFO,
            f"Received message {message}"
        )

        if message_type == CMD:
            self.message_handler.handle_command(content, data)
        elif message_type == MSG:
            self.message_handler.handle_message(content, data)
        else:
            get_logger(__name__).log(
                logging.ERROR,
                f"Unknown message type"
            )
            raise
    
    def send_message(self,client,message):
        self.socketio.emit(client,message)

        get_logger(__name__).log(logging.INFO,
                                 f"Sent message {message} to client {client}")