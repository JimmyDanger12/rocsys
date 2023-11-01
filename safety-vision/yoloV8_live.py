import cv2
import argparse
from ultralytics import YOLO
import supervision as sv
import numpy as np
import json
import socketio
import sys

FLASK_URL = "http://192.168.137.2:4444"
CONFIDENCE_MIN = 0.4
FIELD_MESSAGE_TYPE = "message_type"
FIELD_CONTENT = "content"
FIELD_DATA = "data"
MST_MSG = "msg"
CT_SAFETY = "safety_detection"
MSG_FOREIGN = "detection_foreign"

RES_START = 1
RES_END = 2
RES_FOREIGN = 0

ZONE_POLYGON = np.array([
    [0, 0],
    [0.5, 0],
    [0.5, 1],
    [0, 1]
])

SEND_MESSAGES = False

sio = socketio.Client()

def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="YOLOv8 live")
    parser.add_argument(
        "--webcam-resolution", 
        default=[1280, 720], 
        nargs=2, 
        type=int
    )
    args = parser.parse_args()
    return args


def show_camera(frame, model, detections, box_annotator, zone):
    labels = [
        f"{model.names[class_id]} {confidence:0.4f}"
        for _,_,confidence, class_id,_
        in detections
    ]
    frame = box_annotator.annotate(
        scene=frame, 
        detections=detections, 
        labels=labels
    )
    zone.trigger(detections=detections)      
    cv2.imshow("yolov8", frame)
    return


def send_message(output=dict):
    print(f"Sending message: {output}")
    sio.emit("message_output",json.dumps(output))

def on_connect():
    print("Connected")

def on_disconnect():
    print("Disconnected")  

def on_receive_message(data):
    print("Received message:",data)
    if data == "start_detection":
        global SEND_MESSAGES
        SEND_MESSAGES = True
    elif data == "stop_detection":
        SEND_MESSAGES = False

if __name__ == "__main__":
    args = parse_arguments()
    frame_width, frame_height = args.webcam_resolution

    cap = cv2.VideoCapture(1)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, frame_width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, frame_height)

    model = YOLO("yolov8s.pt")
    initOD = False
    url = FLASK_URL
    show = 0
    names = model.names

    box_annotator = sv.BoxAnnotator(
        thickness=2,
        text_thickness=2,
        text_scale=1
    )

    zone_polygon = (ZONE_POLYGON * np.array(args.webcam_resolution)).astype(int)
    zone = sv.PolygonZone(polygon=zone_polygon, frame_resolution_wh=tuple(args.webcam_resolution))
    
    sio.connect(FLASK_URL)
    sio.on("connect",on_connect)
    sio.on("disconnect",on_disconnect)
    sio.on("message_safety",on_receive_message)
    sio.on("message_all",on_receive_message)

    output = {
        FIELD_MESSAGE_TYPE: MST_MSG,
        FIELD_CONTENT: CT_SAFETY,
        FIELD_DATA: {}
    }

    counter = 0
    while (show != 1 and show != 2):
        show = input("Show safety camera [1 = yes, 2 = no]: ")
        show = int(show)


    while True:       
        ret, frame = cap.read()
        initOD = 0
        personFound = False 
        frame = cv2.flip(frame[:, 150:550],0) # changed for frame size

        #Let machine know if safety camera is available
        if not ret:
            output[FIELD_DATA] = {
                "message": "No safety camera connected"
            }
            break
        
        #Let machine know safety detection has started
        if counter == 0:
            output[FIELD_DATA] = {
                "result": RES_START,
                "message": "Safety detection started"
            }
            send_message(output)

        result = model(frame, agnostic_nms=True, verbose=False, conf = 0.4)[0]
        detections = sv.Detections.from_ultralytics(result)
        
        # Display camera frame if 1 has been chosen
        if(show == 1):
            show_camera(frame, model, detections, box_annotator, zone)

        #Add +1 to counter so machine won't send new available info
        counter += 1
         
        # Send message if person is detected
        for r in result:
            for c in r.boxes.cls:
                if c == 0:
                    personFound = True
                    confidence = r.boxes.conf.item()
                    output[FIELD_DATA] = {
                        "result": RES_FOREIGN,
                        "object": {
                            "name": names[int(c)],
                            "confidence": confidence
                        },
                        "message": f"Foreign object detected: {names[int(c)]}, {round(confidence*100,2)}%"
                    }
                    if SEND_MESSAGES:
                        send_message(output)
                    SEND_MESSAGES = False

                    #don't use for now
                    """initOD = input("reinitialize safety camera press 1:\n")
                    initOD = int(initOD)
                    if (initOD == 1):                    
                        output[FIELD_DATA] = {
                            "result": RES_FOREIGN,
                            "object": {
                                "name": names[int(c)]
                                #"confidence": r.boxes.conf
                            },
                            "message": "Camera reinitialized by user input "
                        }
                        send_message(output)"""
                    break

            if (personFound == True):
                break
        
        if (cv2.waitKey(1) == 27):
            break

    output[FIELD_MESSAGE_TYPE] = MST_MSG
    output[FIELD_DATA] = {
            "result": RES_END,
            "message": "Safety detection finished"
        }
    send_message(url,output)

    cap.release()
    cv2.destroyAllWindows()
    sys.exit()