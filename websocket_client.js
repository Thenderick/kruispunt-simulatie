class websocketClient{
    constructor(sessionID){
        this.callbacks = {};
        this.sessionID = sessionID;
        this.client = new WebSocket("ws://keyslam.com:8080");
        this.client.onopen = event => this.#on_open(event);
        this.client.onmessage = event => this.#on_message(event);
    }

    send(message){
        this.client.send(message);
    }

    #on_open(event){
        const startup = {
            eventType: "CONNECT_SIMULATOR",
            data: {
                sessionName: this.sessionID,
                sessionVersion: 1,
                "discardParseErrors" : false,  
                "discardEventTypeErrors" : false, 
                "discardMalformedDataErrors" : false, 
                "discardInvalidStateErrors" : false, 
            }
        };
        this.client.send(JSON.stringify(startup));
    }

    #on_message(event){
        const response = JSON.parse(event.data);
        this.#parse_message(response);
    }

    #parse_message(msg){
        const eventType = msg["eventType"];
        if (eventType in this.callbacks){
            this.callbacks[eventType](msg.data || "")
        }
    }

    add_callback(key, callback){
        this.callbacks[key] = callback;
    }
}