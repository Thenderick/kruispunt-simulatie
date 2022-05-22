import json
from typing import Callable
import websocket

class server:
    def __init__(self, session_id: str):
        # websocket.enableTrace(True)
        self.callbacks = {}
        self.session_id = session_id
        self.server = websocket.WebSocketApp("ws://keyslam.com:8080/",on_open=self.__on_open, on_message=self.__on_message)

    def __on_open(self, ws: websocket):
        startup_call = {
        "eventType": "CONNECT_CONTROLLER",
            "data": {
                "sessionName": self.session_id,
                "sessionVersion": 1,
                "discardParseErrors" : False,  
                "discardEventTypeErrors" : False, 
                "discardMalformedDataErrors" : False, 
                "discardInvalidStateErrors" : False, 
            }
        }
        ws.send(json.dumps(startup_call))

    def start_server(self):
        self.server.run_forever()

    def __on_message(self, ws: websocket, message: str):
        parsed_message = json.loads(message)
        self.__parse_message(parsed_message)

    def __parse_message(self, msg: dict):
        eventType = msg["eventType"]
        if eventType in self.callbacks.keys():
            if "data" in msg.keys():
                self.callbacks[eventType](msg["data"])
            else:
                self.callbacks[eventType]({})

    def add_callback(self, key:str, callback: Callable[[dict], None]):
        self.callbacks[key] = callback
    
    def sendstr(self, message: str):
        self.server.send(message)

    def send(self, eventType: str, data: dict):
        if data == {}:
            self.sendstr(json.dumps({
                "eventType": eventType
            }))
        else:
            self.sendstr(json.dumps({
                "eventType": eventType,
                "data":data
            }))
