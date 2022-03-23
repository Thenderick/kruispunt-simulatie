from server import *
import json

def on_start(data: dict):
    print("doet het!")
    set_auto_state = {
        "eventType" : "SET_AUTOMOBILE_ROUTE_STATE", 
        "data" : { 
            "routeId" : 1, 
            "state" : "GREEN"
        }
    }
    localserver.send(json.dumps(set_auto_state))

def on_stop(data: dict):
    print("gestopt")

def on_entity_entered_zone(data: dict):
    print("entity entered zone:")
    print(data)

if __name__ == "__main__":
    localserver = server("RickTest")
    localserver.add_callback("SESSION_START", on_start)
    localserver.add_callback("SESSION_STOP", on_stop)
    localserver.add_callback("ENTITY_ENTERED_ZONE", on_entity_entered_zone)
    localserver.start_server()