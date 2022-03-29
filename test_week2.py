import time
from server import *
import json

all_routes=[1,2,3,4,5,7,8,9,10,11,12,15,21,22,23,24,31,32,33,34,35,36,37,38]

car_routes = {
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
    15:"RED"
}
cyclist_routes = {
    21:"RED",
    22:"RED",
    23:"RED",
    24:"RED"
}
pedestrian_routes = {
    31:"RED",
    32:"RED",
    33:"RED",
    34:"RED",
    35:"RED",
    36:"RED",
    37:"RED",
    38:"RED",
}

def set_light(type:str, route:int, state:str):
    event_types = {"car":"SET_AUTOMOBILE_ROUTE_STATE", "cyclist":"SET_CYCLIST_ROUTE_STATE", "pedestrian":"SET_PEDESTRIAN_ROUTE_STATE"}
    return json.dumps({
        "eventType":event_types[type],
        "data":{
            "routeId":route,
            "state":state
        }
    })

def on_start(data):
    print("stage1")
    for (route, state) in car_routes.items():
        car_routes[route] = "RED"
        localserver.send(set_light("car", route, car_routes[route]))
    for (route, state) in cyclist_routes.items():
        cyclist_routes[route] = "RED"
        localserver.send(set_light("cyclist", route, cyclist_routes[route]))
    for (route, state) in pedestrian_routes.items():
        pedestrian_routes[route] = "RED"
        localserver.send(set_light("pedestrian", route, pedestrian_routes[route]))

    time.sleep(10)

    print("stage2")
    for (route, state) in car_routes.items():
        car_routes[route] = "GREEN"
        localserver.send(set_light("car", route, car_routes[route]))
    for (route, state) in cyclist_routes.items():
        cyclist_routes[route] = "GREEN"
        localserver.send(set_light("cyclist", route, cyclist_routes[route]))
    for (route, state) in pedestrian_routes.items():
        pedestrian_routes[route] = "GREEN"
        localserver.send(set_light("pedestrian", route, pedestrian_routes[route]))

    time.sleep(10)

    print("stage3")
    for (route, state) in car_routes.items():
        car_routes[route] = "ORANGE"
        localserver.send(set_light("car", route, car_routes[route]))
    for (route, state) in cyclist_routes.items():
        cyclist_routes[route] = "ORANGE"
        localserver.send(set_light("cyclist", route, cyclist_routes[route]))
    for (route, state) in pedestrian_routes.items():
        pedestrian_routes[route] = "BLINKING"
        localserver.send(set_light("pedestrian", route, pedestrian_routes[route]))
    
    time.sleep(10)

    green = [1,2,8,22,33,34]

    print("stage4")
    for (route, state) in car_routes.items():
        if route in green:
            car_routes[route] = "GREEN"
        else:
            car_routes[route] = "RED"
        localserver.send(set_light("car", route, car_routes[route]))
    for (route, state) in cyclist_routes.items():
        if route in green:
            cyclist_routes[route] = "GREEN"
        else:
            cyclist_routes[route] = "RED"
        localserver.send(set_light("cyclist", route, cyclist_routes[route]))
    for (route, state) in pedestrian_routes.items():
        if route in green:
            pedestrian_routes[route] = "GREEN"
        else:
            pedestrian_routes[route] = "RED"
        localserver.send(set_light("pedestrian", route, pedestrian_routes[route]))

if __name__ == "__main__":
    localserver = server("RickTest")
    localserver.add_callback("SESSION_START", on_start)
    localserver.start_server()
