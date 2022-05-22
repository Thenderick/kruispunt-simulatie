import time
from server import *
import logging
import threading

FORMAT = '[[%(levelname)s]] %(asctime)s - %(message)s'
logging.basicConfig(format=FORMAT, filename='kruispunt.debug.log', level=logging.DEBUG)
logging.basicConfig(format=FORMAT, filename='kruispunt.info.log', level=logging.INFO)
logging.basicConfig(format=FORMAT, filename='kruispunt.error.log', level=logging.ERROR)

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
    41:"RED",
    42:"RED"
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

# nice

# bijhouden brug state
bridge_state = 'DOWN'

# Amount of updates per second
UPDATE_RATE = 20

# evt extension time?
GREEN_TIME = dict.fromkeys([1,2,3,4,5,7,8,9,10,11,12], 8)           # auto routes
GREEN_TIME.update(dict.fromkeys([15], 6))                           # bus route
GREEN_TIME.update(dict.fromkeys([21,22,23,24],8))                   # fiets route
GREEN_TIME.update(dict.fromkeys([31,32,33,34,35,36,37,38], 6))      # voetganger routes
GREEN_TIME.update(dict.fromkeys([41,42], 10))                       # boten

ORANGE_TIME = dict.fromkeys([2,5,8,11], 4)                          # rechtdoorgaande auto routes
ORANGE_TIME.update(dict.fromkeys([1,3,4,7,9,10,12], 3))             # afslaande auto routes
ORANGE_TIME.update(dict.fromkeys([21,22,23,24], 3))                 # fiets routes
ORANGE_TIME.update(dict.fromkeys([15], 4))                          # bus route
ORANGE_TIME.update(dict.fromkeys([31,32,33,34,35,36,37,38], 3.5))   # voetgangers
ORANGE_TIME.update(dict.fromkeys([41,42], 0))                       # om error te voorkomen

CLEARING_TIME = 2

controller_active = True
def controller_loop():
    while controller_active:
        update_lights()
        update_queue()
        time.sleep(1/UPDATE_RATE)

# {routeID (int) : count (int)} template voor items pushed/popped
traffic_queue = {}
boat_queue = {}

active_lights = []
loop_thread = threading.Thread(target=controller_loop)
queue_lock = threading.Lock()

def update_lights():
    for light in active_lights:
        if light['time'] <= 0:
            if light['state'] == "GREEN":
                # alle routes die geen boot zijn gaan na groen op oranje/knipper
                if light['route'] < 40:
                    add_to_active(light['route'], "ORANGE" if light['route'] < 30 else "BLINKING")
                    active_lights.remove(light)
                else: # route is voor boten
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
    if len(traffic_queue) > 0:
        route, _ = list(traffic_queue.items())[0]
        if can_go_green(route):
            add_to_active(route, "GREEN")
            del traffic_queue[route]

    global bridge_state
    if bridge_state == 'UP':
        if len(boat_queue) > 0:
            route, _ = list(boat_queue.items())[0]
            logging.debug(" bridge queue: %s | route: %s", boat_queue, route)
            if can_go_green(route):
                add_to_active(route, "GREEN")
                del boat_queue[route]
        elif current_state[41]!='GREEN' and current_state[42]!="GREEN":
            request_bridge_water_empty()
            bridge_state = 'CLOSING'

    if len(boat_queue) > 0:
        if bridge_state == "DOWN":
            localserver.send("SET_BRIDGE_WARNING_LIGHT_STATE",
            {
                "state" : "ON"
            })

            localserver.send("REQUEST_BRIDGE_ROAD_EMPTY",{})
            bridge_state = "OPENING"

event_types = ["SET_AUTOMOBILE_ROUTE_STATE","SET_AUTOMOBILE_ROUTE_STATE","SET_CYCLIST_ROUTE_STATE","SET_PEDESTRIAN_ROUTE_STATE","SET_BOAT_ROUTE_STATE"]
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
    timetable = {
        'CLEARING':CLEARING_TIME,
        'GREEN':GREEN_TIME[route],
        'ORANGE':ORANGE_TIME[route],
        'BLINKING':ORANGE_TIME[route]
    }
    tmp = {'route':route,'state':state, 'time': timetable[state]*UPDATE_RATE}
    active_lights.append(tmp)
    logging.debug("route: %s set to %s", route, state)
    localserver.send(get_event_type(route),
    {
        "routeId":route,
        "state":"RED" if state == 'CLEARING' else state
    })
    current_state[route] = state

def on_start(data):
    logging.info("session start!")
    global controller_active
    controller_active = True   
    loop_thread.start()

def on_stop(data):
    logging.info("SESSION STOPPED")
    exit()
    

def on_entity_entered(data):
    routeID = data['routeId']
    sensorID = data['sensorId']
    logging.debug("Entity entered on %s : %s", routeID, sensorID)
    #car
    if routeID < 20:
        if current_state[routeID] == 'RED':
            if routeID not in traffic_queue:
                traffic_queue[routeID] = 1
            else:
                traffic_queue[routeID] += 1

    #bike
    elif routeID < 30:
        if current_state[routeID]  == 'RED':
            if routeID not in traffic_queue:
                traffic_queue[routeID] = 1

    #pedestrian
    elif routeID < 40:
        if current_state[routeID]  == 'RED':
            if routeID not in traffic_queue:
                traffic_queue[routeID] = 1

    #boat
    else:
        global bridge_state
        if routeID not in boat_queue:
            boat_queue[routeID] = 1
        if bridge_state == "DOWN":
            localserver.send("SET_BRIDGE_WARNING_LIGHT_STATE",
            {
                "state" : "ON"
            })

            localserver.send("REQUEST_BRIDGE_ROAD_EMPTY",{})
            bridge_state = "OPENING"

def on_entity_exited(data):
    logging.debug("%s exited zone", data)

def on_acknowledge_empty_road(data):
    logging.debug('acknowledged empty road')
    localserver.send("REQUEST_BARRIERS_STATE",
    {
        "state" : "DOWN"
    })

def on_acknowledge_barrier_state(data):
    logging.debug('acknowledged barrier state: %s', data["state"])
    if data["state"] == "UP":
        localserver.send('SET_BRIDGE_WARNING_LIGHT_STATE',
        {
            'state': 'OFF'
        })
        global bridge_state
        bridge_state = "DOWN"
    else: # state == "DOWN"
        route, _ = list(boat_queue.items())[0]
        localserver.send("SET_BOAT_ROUTE_STATE",
        {
            "routeId" : route,
            "state" : "GREENRED"
        })

        current_state[route] = "GREENRED"
        localserver.send("REQUEST_BRIDGE_STATE",
        {
            "state" : "UP"
        })

def on_acknowledge_bridge_state(data):
    logging.debug('acknowledged bridge state: %s', data["state"])
    if data["state"] == "UP":
        global bridge_state
        bridge_state = 'UP'

    else: # state == "DOWN"
        localserver.send('REQUEST_BARRIERS_STATE',
        {
            'state': 'UP'
        })

def on_acknowledge_bridge_water_empty(data):
    logging.debug('acknowledged bridge water empty')
    for route in [41,42]:
        if current_state[route] != "RED":
            localserver.send('SET_BOAT_ROUTE_STATE',
            {
                'routeId': route, 
                'state': 'RED'
            })
            current_state[route] = "RED"
    localserver.send('REQUEST_BRIDGE_STATE',
    {
        'state': 'DOWN'
    })

def request_bridge_water_empty():
    localserver.send("REQUEST_BRIDGE_WATER_EMPTY",{})

def on_error(data):
    logging.error("ERROR: [[[%s]]]", data)

if __name__ == "__main__":
    localserver = server("test69")
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

    # start server
    localserver.start_server()