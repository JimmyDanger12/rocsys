#!usr/bin/env python

"""
This script will start the server
By default the server is located at localhost on port 4444.
"""

from server import Server
from globalconfig import GlobalConfig

DEFAULT_CONFIG_PATH = "config.ini"

if __name__ == "__main__":
    server = Server()
    config = GlobalConfig(DEFAULT_CONFIG_PATH)

    server.start(config)