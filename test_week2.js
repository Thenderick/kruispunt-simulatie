const simulation_client = new websocketClient("RickTest");
simulation_client.add_callback("SESSION_START", start);
simulation_client.add_callback("SESSION_STOP", stop);
simulation_client.add_callback("SET_AUTOMOBILE_ROUTE_STATE", log_data);
simulation_client.add_callback("SET_CYCLIST_ROUTE_STATE", log_data);
simulation_client.add_callback("SET_PEDESTRIAN_ROUTE_STATE", log_data);

function log_data(data){
    console.log(data);
}

function stop(data){
    console.log("sessie gestopt");
}

function start(data){
    console.log("sessie gestart!");
}