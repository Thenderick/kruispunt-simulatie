import time
from server import *
import json
import threading

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
bridge_state = 'DOWN'

# Amount of updates per second
UPDATE_RATE = 20

GREEN_TIME = 6

ORANGE_TIME = 4

BOAT_TIME = 10

controller_active = True
def controller_loop():
    while controller_active:
        update_lights()
        update_queue()
        time.sleep(1/UPDATE_RATE)

# {routeID (int) : count (int)} template voor items pushed/popped
traffic_queue = {}
boat_queue = {}
# time is in met tien vermenigvuldigd en is dus zoveel keer 0,1 seconden die het stoplicht op kleur moet. (stomme floating point precision)
active_lights = []
loop_thread = threading.Thread(target=controller_loop)
queue_lock = threading.Lock()

def update_lights():
    for light in active_lights:
        if light['time'] <= 0:
            if light['state'] == "GREEN":
                if light['route'] < 40:
                    add_to_active(light['route'], "ORANGE" if light['route'] < 30 else "BLINKING")
                    active_lights.remove(light)
                else:
                    add_to_active(light['route'], 'CLEARING')
                    active_lights.remove(light)
            elif light['state'] in ['ORANGE', 'BLINKING']:
                add_to_active(light['route'], 'CLEARING')
                active_lights.remove(light)
            else: #if state == 'CLEARING'
                current_state[light['route']] = 'RED'
                active_lights.remove(light)
        else:
            light['time'] -= 1

def update_queue():
    # don't even try.... doorstroming is een hoax.... 
    # print(f"current queue: {traffic_queue}", flush=True)
    if len(traffic_queue) > 0:
        # with queue_lock:
        #     for route, count in traffic_queue.items():
        #         if can_go_green(route):
        #             add_to_active(route, "GREEN")
        #             del traffic_queue[route]
        route, count = list(traffic_queue.items())[0]
        if can_go_green(route):
            add_to_active(route, "GREEN")
            del traffic_queue[route]

    if bridge_state == 'UP':
        if len(boat_queue) > 0:
            route, _ = list(boat_queue.items())[0]
            if can_go_green(route):
                add_to_active(route, "GREEN")
                del traffic_queue[route]
        else:
            request_bridge_water_empty()
            bridge_state = 'DOWN'

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

def add_to_active(route:int, state:str):
    if state == 'CLEARING':
        tmp = {'route':route,'state':state, 'time': 6*UPDATE_RATE}
        active_lights.append(tmp)
        print(f"route: {route} set to {state}")
        localserver.send(
            json.dumps({
                "eventType":get_event_type(route),
                "data":{
                    "routeId":route,
                    "state":"RED"
                }
            })
        )
        current_state[route] = state
    else:
        tmp = {'route':route,'state':state, 'time': GREEN_TIME*UPDATE_RATE if state == "GREEN" else ORANGE_TIME*UPDATE_RATE}
        active_lights.append(tmp)
        print(f"route: {route} set to {state}")
        localserver.send(
            json.dumps({
                "eventType":get_event_type(route),
                "data":{
                    "routeId":route,
                    "state":state
                }
            })
        )
        current_state[route] = state

def on_start(data):
    controller_active = True
    loop_thread.start()
    print("session start!")

def on_stop(data):
    controller_active = False
    loop_thread.join()
    traffic_queue.clear()
    active_lights.clear()
    print("SESSION STOPPED")

def on_entity_entered(data):
    # with queue_lock:
    print(f"{data}", flush=True)
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
        if current_state[routeID] == "RED":
            if routeID not in traffic_queue:
                traffic_queue[routeID] = 1

    #pedestrian
    elif routeID < 40:
        if current_state[routeID] == "RED":
            if routeID not in traffic_queue:
                traffic_queue[routeID] = 1

    #boat
    else:
        if routeID not in boat_queue:
            boat_queue[routeID] = 1
            localserver.send(
                json.dumps({
                    "eventType": "SET_BRIDGE_WARNING_LIGHT_STATE",
                    "data" : {
                        "state" : "ON"
                    }
                })
            )
            localserver.send(
                json.dumps({ 
                    "eventType" : "REQUEST_BRIDGE_ROAD_EMPTY",  
                })
            )

def on_entity_exited(data):
    print(f"{data} exited zone")

def on_acknowledge_empty_road(data):
    localserver.send(
        json.dumps({
            "eventType" : "REQUEST_BARRIERS_STATE",
            "data" : {
                "state" : "DOWN"
            }
        })
    )

def on_acknowledge_barrier_state(data):
    if data["state"] == "UP":
        localserver.send(
            json.dumps({
                'eventType': 'SET_BRIDGE_WARNING_LIGHT_STATE',
                'data':{
                    'state': 'OFF'
                }
            })
        )
    else: # state == "DOWN"
        route, _ = list(boat_queue.items())[0]
        localserver.send(
            json.dumps({
                "eventType" : "SET_BOAT_ROUTE_STATE",
                "data" : {
                    "routeId" : route,
                    "state" : "GREENRED"
                }
            })
        )
        current_state[route] = "GREENRED"
        localserver.send(
            json.dumps({
                "eventType" : "REQUEST_BRIDGE_STATE",
                "data" : {
                    "state" : "UP"
                }
            })
        )

def on_acknowledge_bridge_state(data):
    if data["state"] == "UP":
        bridge_state = 'UP'

    else: # state == "DOWN"
        localserver.send(
            json.dumps({
                'eventType': 'REQUEST_BARRIER_STATE',
                'data':{
                    'state': 'UP'
                }
            })
        )

def on_acknowledge_bridge_water_empty(data):
    for route in [41,42]:
        localserver.send(
            json.dumps({
                'eventType': 'SET_BOAT_ROUTE_STATE',
                'data':{
                    'routeId': route,
                    'state': 'RED'
                }
            })
        )

    localserver.send(
            json.dumps({
                'eventType': 'REQUEST_BRIDGE_STATE',
                'data':{
                    'state': 'DOWN'
                }
            })
        )

def request_bridge_water_empty():
    localserver.send(
        json.dumps({
            "eventType": "REQUEST_BRIDGE_WATER_EMPTY"
        })
    )

def on_error(data):
    print(f"{data}")

if __name__ == "__main__":
    localserver = server("Justin_mag_dit_nooit_zien!")
    # 'normaal' verkeer
    localserver.add_callback("SESSION_START", on_start)
    localserver.add_callback("SESSION_STOP", on_stop)
    localserver.add_callback("ENTITY_ENTERED_ZONE", on_entity_entered)
    localserver.add_callback("ENTITY_EXITED_ZONE", on_entity_exited)

    # boot verkeer
    localserver.add_callback("ACKNOWLEDGE_BRIDGE_ROAD_EMPTY", on_acknowledge_empty_road)
    localserver.add_callback("ACKNOWLEDGE_BARRIERS_STATE", on_acknowledge_barrier_state)
    localserver.add_callback("ACKNOWLEDGE_BRIDGE_STATE", on_acknowledge_bridge_state)
    localserver.add_callback("ACKNOWLEDGE_BRIDGE_WATER_EMPTY", on_acknowledge_bridge_water_empty)

    # error handling
    localserver.add_callback("ERROR_INVALID_STATE", on_error)
    localserver.add_callback("ERROR_MALFORMED_MESSAGE", on_error)
    localserver.add_callback("ERROR_UNKNOWN_EVENT_TYPE", on_error)
    localserver.add_callback("ERROR_NOT_PARSEABLE", on_error)

    localserver.start_server()