const simulation_client = new websocketClient("RickTest");
simulation_client.add_callback("SESSION_START", start);
simulation_client.add_callback("SESSION_STOP", stop);
simulation_client.add_callback("SET_AUTOMOBILE_ROUTE_STATE", set_auto_route_state);

function set_auto_route_state(data){
    console.log("auto route changed!");
    console.log(data);
    const zone = {
        "eventType" : "ENTITY_ENTERED_ZONE",
        "data" : {
            "routeId" : 1,
            "sensorId" : 2,
        } 
    } 
    simulation_client.send(JSON.stringify(zone))
}

function stop(data){
    console.log("sessie gestopt");
}

function start(data){
    console.log("sessie gestart!");
}