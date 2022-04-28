import time
from server import *
import json
import queue
import threading
import logging

current_state = {
    1:"RED",
    2:"RED",
    3:"RED",
    4:"RED",
    5:"RED",
    7:"RED",
    8:"RED",
    9:"RED",
    10:"RED",
    11:"RED",
    12:"RED",
    15:"RED",
    21:"RED",
    22:"RED",
    23:"RED",
    24:"RED",
    31:"RED",
    32:"RED",
    33:"RED",
    34:"RED",
    35:"RED",
    36:"RED",
    37:"RED",
    38:"RED",
}

crosses_with = {
    1: [5,9,21,24,31,38],
    2: [5,9,10,11,12,21,23,31],
    3: [5,7,8,11,12,15,21,22,31,34],
    4: [8,12,15,21,22,32,33],
    5: [1,2,3,8,9,11,12,15,22,23,24,33,36,38],
    7: [3,11,15,22,23,34,35],
    8: [3,4,5,11,12,21,23,32,35],
    9: [1,2,5,11,12,23,24,35,38],
    10:[2,23,24,36,37],
    11:[2,3,5,7,8,9,15,22,24,34,37],
    12:[2,3,4,5,8,9,21,24,32,37],
    15:[3,4,5,7,11],
    21:[1,2,3,4,8,12],
    22:[3,4,5,7,11],
    23:[2,5,7,8,9,10],
    24:[1,5,9,10,11,12],
    31:[1,2,3],
    32:[4,8,12],
    33:[4,5],
    34:[3,7,11],
    35:[7,8,9],
    36:[2,5,10],
    37:[10,11,12],
    38:[1,5,9],
    41:[42],
    42:[41],
}

def controller_loop():
    while True:
        update_lights()
        update_queue()
        time.sleep(0.1)

# {routeID (int) : count (int)} template voor items pushed/popped
traffic_queue = {}
# time is in met tien vermenigvuldigd en is dus zoveel keer 0,1 seconden die het stoplicht op kleur moet. (stomme floating point precision)
active_lights = []
loop_thread = threading.Thread(target=controller_loop)

def update_lights():
    for light in active_lights:
        if light['time'] <= 0:
            if light['state'] == "GREEN":
                add_to_active(light['route'], "ORANGE" if light['route'] < 30 else "BLINKING", get_event_type(light['route']))
                active_lights.remove(light)
            else:
                localserver.send(
                    json.dumps({
                        "eventType":get_event_type(light['route']),
                        "data":{
                            "routeId":light['route'],
                            "state":"RED"
                        }
                    })
                )
                current_state[light['route']] = 'RED'
                active_lights.remove(light)
        else:
            light['time'] -= 1


def update_queue():
    # print(f"current queue: {traffic_queue}", flush=True)
    if len(traffic_queue) > 0:
        route, count = list(traffic_queue.items())[0]
        if can_go_green(route):
            add_to_active(route, "GREEN", get_event_type(route))
            del traffic_queue[route]

event_types = ["SET_AUTOMOBILE_ROUTE_STATE","SET_AUTOMOBILE_ROUTE_STATE","SET_CYCLIST_ROUTE_STATE","SET_PEDESTRIAN_ROUTE_STATE"]
def get_event_type(route:int):
    first_num = route // 10
    return event_types[first_num]

def do_routes_cross(route_a:int, route_b:int):
    return route_b in crosses_with[route_a]

def can_go_green(route:int):
    for i in crosses_with[route]:
        if current_state[i] != "RED":
            return False
    return True

def add_to_active(route:int, state:str, eventType:str):
    tmp = {'route':route,'state':state, 'time': 60 if state == "GREEN" else 40}
    active_lights.append(tmp)
    localserver.send(
        json.dumps({
            "eventType":eventType,
            "data":{
                "routeId":route,
                "state":state
            }
        })
    )
    current_state[route] = state

def on_start(data):
    loop_thread.start()
    print("session start!")

def on_stop(data):
    loop_thread.join()
    traffic_queue.clear()
    active_lights.clear()

def on_entity_entered(data):
    print(data, flush=True)
    routeID = data['routeId']
    sensorID = data['sensorId']
    #car
    if routeID < 20:
        if current_state[routeID] == "RED":
            # afhankelijk van welke zone geïmplementeerd is
            if sensorID % 2 == 1:
                if routeID not in traffic_queue:
                    traffic_queue[routeID] = 1
                else:
                    traffic_queue[routeID] += 1

    #bike
    elif routeID < 30:
        pass

    #pedestrian
    elif routeID < 40:
        pass

    # boot
    else:
        pass

def on_entity_exited(data):
    print(f"{data} exited zone")

def on_error(data):
    print(data)

if __name__ == "__main__":
    localserver = server("jelkerick")
    localserver.add_callback("SESSION_START", on_start)
    localserver.add_callback("SESSION_STOP", on_stop)
    localserver.add_callback("ENTITY_ENTERED_ZONE", on_entity_entered)
    localserver.add_callback("ENTITY_EXITED_ZONE", on_entity_exited)

    localserver.add_callback("ERROR_INVALID_STATE", on_error)
    localserver.add_callback("ERROR_MALFORMED_MESSAGE", on_error)
    localserver.add_callback("ERROR_UNKNOWN_EVENT_TYPE", on_error)
    localserver.add_callback("ERROR_NOT_PARSEABLE", on_error)

    localserver.start_server()