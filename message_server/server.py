from flask import Flask, request, jsonify
import logging
from message_server.globalconfig import GlobalConfig
from message_server.roc_logging import setup_logging, get_logger
from message_server.robot_controller import RobotController
from message_server.message_handler import MessageHandler

FIELD_MESSAGE_TYPE = "message_type"
FIELD_CONTENT = "content"
FIELD_DATA = "data"
FIELD_MESSAGE = "message"
FIELD_ERROR = "error"
FIELD_RESPONSE = "response"
CMD = "cmd"
MSG = "msg"

class Server():
    """
    This class implements a Flask server used to send/receive
    messages from the ROCSYS bash script and starts the message and command handling.

    
    """

    def __init__(self):
        self.server = None
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

        host = config["SERVERCONFIG", "host"]
        port = config["SERVERCONFIG", "port"]
        debug = eval(config["SERVERCONFIG", "debug"])
        route = config["SERVERCONFIG", "route"]

        home_position = config["ROBOT", "home_position"]
        fsp = config["ROBOT", "front_socket_position"]
        robot_ip = config["ROBOT", "ip"]
        robot_port = config["ROBOT", "port"]
        detection_acc = eval(config["ROBOT", "accurate_detection"])
        log_detection = eval(config["ROBOT","log_detection"])

        self.robot_controller = RobotController(robot_ip, robot_port, home_position, fsp, detection_acc, log_detection)
        self.message_handler = MessageHandler(self, self.robot_controller)

        @self.server.route(route, methods=["POST"])
        def receive_docker_output():
            """
            This is the default route for the Flask server 
            to listen to messages from the docker output

            Returns:
                returns a message to original sender
            """
            response = None

            message_raw = request.get_json()
            try:
                response = self.handle_message(message_raw)
                get_logger(__name__).log(logging.INFO,
                                         f"Returned response: {response}")
                
                if response == None:
                    return jsonify({FIELD_MESSAGE: "Docker output received successfully"}), 200
                else:
                    return jsonify({FIELD_MESSAGE: "Docker output received successfully", FIELD_RESPONSE: response}), 200
            except Exception as e:
                get_logger(__name__).error(e)
                return jsonify({FIELD_ERROR: str(e)}), 500
        
        try:
            self.server.run(host=host, port=port, debug=debug)
            
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
        response = None
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
            response = self.message_handler.handle_command(content, data)
        elif message_type == MSG:
            response = self.message_handler.handle_message(content, data)
        else:
            get_logger(__name__).log(
                logging.ERROR,
                f"Unknown message type"
            )
            raise
            
        return response