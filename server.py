from flask import Flask, request, jsonify
import json
import logging
from globalconfig import GlobalConfig
from roc_logging import setup_logging, get_logger
from robot import RobotController
from message_handler import MessageHandler

FIELD_MESSAGE_TYPE = "message_type"
FIELD_CONTENT = "content"
FIELD_DATA = "data"
FIELD_MESSAGE = "message"
FIELD_ERROR = "error"
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
        self.command_handler = None

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
        home_position = config["ROBOT", "home"]
        global_speed = config["ROBOT", "global_speed"]

        self.robot_controller = RobotController(home_position, global_speed)
        self.message_handler = MessageHandler(self, self.robot_controller)

        @self.server.route(route, methods=["POST"])
        def receive_docker_output():
            """
            This is the default route for the Flask server 
            to listen to messages from the docker output

            Returns:
                returns a message to original sender
            """

            message_raw = request.get_json()
            try:
                self.handle_message(message_raw)
                return jsonify({FIELD_MESSAGE: "Docker output received successfully"}), 200
            except Exception as e:
                get_logger(__name__).error(e)
                return jsonify({FIELD_ERROR: str(e)}), 500
        
        try:
            self.server.run(host=host, port=port, debug=debug)
        except KeyboardInterrupt as k:
            pass
        except Exception as e:
            get_logger(__name__).error(e)
            raise
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