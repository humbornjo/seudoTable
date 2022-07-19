var voidCallback = function(e) { };

class EventSubscriber {
    constructor(onclose=undefined) {
        if (onclose == undefined) {
            onclose = function (e) {
                console.error('Connection closed by server');
            };
        }
        console.assert(onclose instanceof Function);
        
        this.socket = new WebSocket('ws://' + window.location.host + '/ws/internal/general/');
        this.callbacks = new Map([
            ["task_end", voidCallback],
            ["completed_table", voidCallback],
            ["table_state_changed", voidCallback],
            ["started_process_all", voidCallback],
            ["import_status", voidCallback],
            ["import_progress", voidCallback],
            ["delete_all_finished", voidCallback]
        ]);
        
        this.socket.onmessage = function(e) {
            var data = JSON.parse(e.data);
            var eventName = data["type"];
            
            var callback = this.callbacks.get(eventName);
            if (callback != undefined) {
                callback(data);
            }
        }.bind(this);
        
        this.socket.onclose = onclose;
    }
    
    subscribe(eventName, on_received) {
        console.assert(this.callbacks.has(eventName));
        
        this.callbacks.set(eventName, on_received);
    }
    
    unsubscribe(eventName) {
        console.assert(this.callbacks.has(eventName));
        
        this.callbacks.set(eventName, voidCallback);
    }
}
