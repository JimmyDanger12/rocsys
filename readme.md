# SMR-rocsys EV-charging code

This is a python project written for rocsys as a part of the minor 'Smart manufacturing and robotics' of 'The Hague University of Applied Sciences'.

Project members were:
- Simon Gmeiner
- Luc von Eck
- Ise Kooij
- Donizetta Daffa Aqilla Harley

All code, including documentation with the exeption of parts of the vision code was created by Simon Gmeiner, so inquiries should be documented at 221818@student.hhs.nl. After completion of the project the code will not be maintained or updated. Inquiries will not be answered after completion and evaluation.

## Installation:

- Install DRL-Studio:
    - connect to the homberger hub and robot using their respective ip-addresses
- Install requirements using requirements.txt
  - pip install -r requirements.txt

## Usage:

-  DRL-studio
    - connect to the robot and homberger hub using DRL-studio
    - start setup_robot_server.py in DRL-studio
- Main server
    - start run_server.py
- Safety setup
    - start safety-vision/voloV8_live.py
      - if you want to view the safety detection -> press 1, otherwise 2
- rocsys computer
    - start the docker container
    - start rocsys-files/run_robot_task.py to view the UI and input robot commands

## Logging

The log of the main client is located in logs/backend.log

## Safety-Vision

safety stop definition: interruptable movements are interrupted, and no new movement commands are accepted.

Movements that can be interrupted are:
- plug-in:
        - home to pos1
        - pos1 to fsp
- plug-out:
        - pos1 to home

Movements that cannot be interrupted are:
- plug-in:
        - pos_x to home (intial movement, should be at home position already, except for safety stop and is necessary to accurately determine the defined robot's home position)
        - plug-in (the used commands cannot be executed async, so also cannot be interrupted - also there exists no real safety risk in these small movements already in the socket (5cm))
- plug-out:
        - initial plug-out (as this is a very simple and small movement, that also inherits no real safety risk, interruption is also excluded)
