"use strict";

// random()
String.prototype.random = function(length, chars) {
    var temp = [];
    var chars = chars || this.valueOf() || "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";
    for (var i=0; i<length; i++) {
        var n = Math.floor(Math.random() * chars.length);
        temp.push(chars.charAt(n));
    }
    return temp.join("");
};




/*
 888888ba                    dP   dP   oo                     
 88    `8b                   88   88                          
a88aaaa8P' .d8888b. .d8888b. 88 d8888P dP 88d8b.d8b. .d8888b. 
 88   `8b. 88ooood8 88'  `88 88   88   88 88'`88'`88 88ooood8 
 88     88 88.  ... 88.  .88 88   88   88 88  88  88 88.  ... 
 dP     dP `88888P' `88888P8 dP   dP   dP dP  dP  dP `88888P' 
*/
/**
 * Manages the 'Realtime' connection.
 *
 * This is better than plain SockJS because:
 *  - It integrates tightly with the 'realtime' backend
 *  - The realtime backend can send 'events' which are emitted via Stapes
 *  - It provides a simple 'do' method for RPC with the realtime backend
 *  - It automagically reconnects and handles graceful shutdown
 *  - You don't need to 'connect' - just use it
 *  - It handles timeout and success/error calls
 *
 * Usage:
 *   Camaste.realtime.call(name, args, [success, [error, [timeout]]])
 *
 * Success and Error arguments are callbacks which take two arguments:
 *   function error_or_success (message, rpccall) {...}
 *
 * The `message` param will be the response dictionary from the server
 * or "shutdown" or "timeout" strings in those conditions.
 *
 * `rpccall` param will be the RPC call object with all parameters.
 */
var Camaste_Realtime = Stapes.subclass({
    constructor: function (app) {
        this._sjs = null;
        this._is_open = false;
        this._shutting_down = false;
        this._active = {};
        this._queued = [];

        var self = this;
        app.on('shutdown', function () {
            self._shutting_down = true;
            self.close();
        })
    },

    /**
     * Initialise SockJS connection.
     * During shutdown the connection won't be re-initialised
     */
    _connect: function () {
        if( this._shutting_down == false && this._sjs == null ) {
            var sjs = new SockJS('//' + window.location.host + '/realtime');
            var self = this;
            sjs.onopen = function () {
                self.emit('sockjs.open', sjs);
                self._is_open = true;
                self._tick();
            };
            sjs.onclose = function () {
                self.emit('sockjs.close', sjs);
                self._is_open = false;
                self._sjs = null;
                self._connect();             
            }
            sjs.onmessage = function (msg) {
                self.emit('sockjs.msg', msg);
                self._on_msg(msg);
            }
            this._sjs = sjs;
        }
        return sjs;
    },

    /**
     * Handle messages coming through our SockJS endpoint from the Realtime server
     */
    _on_msg: function (raw_msg) {
        if( raw_msg.type != "message" ) {
            return;
        }

        var msg = null;
        try {
            msg = JSON.parse(raw_msg.data);
        }
        catch( e ) { /* JSON parse error?... aint much we can do here */ }

        if( msg instanceof Object && 'id' in msg && typeof(msg.id) == "string" )  {
            // The ID is a known 'active' message
            if( msg.id in this._active ) {
                var rpc = this._active[msg.id];
                delete this._active[msg.id];

                // When we get a reply like {_:1, ...} then call the 'ok' handler
                if( '_' in msg && msg._ ) {
                    if( rpc.ok ) {
                        rpc.ok(msg, rpc);
                    }
                    this.emit(msg.id, msg);                    
                }
                // Otherwise call the 'error' handler
                else {
                    if( rpc.err ) {
                        rpc.err(msg, rpc);
                    }
                    this.emit(rpc.id + '.error', msg);                    
                }
            } 
            // The ID is unknown - we still emit events
            else {
                // When we get a reply like {_:1, ...} then call the 'ok' handler
                if( '_' in msg && msg._ > 0 ) {
                    this.emit(msg.id, msg);                    
                }
                // Otherwise call the 'error' handler
                else {
                    this.emit(rpc.id + '.error', msg);                    
                }                        
            }
            
        }
    },

    /**
     * Send queued calls 
     */
    _tick: function () {        
        while( this._is_open && this._queued.length && this._shutting_down == false && this._sjs != null ) {
            var rpc = this._queued.pop();        
            this._active[ rpc.id ] = rpc;
            this._sjs.send(JSON.stringify({
                "id": rpc.id,
                "call": rpc.call,
                "args": rpc.args
            }));
        }
    },

    /**
     * Closes the connection
     * + errors any active/sent calls
     * + if shutting down also errors all queued calls
     */
    close: function () {
        if( this._sjs != null ) {            
            this._sjs.close();            
            this._sjs = null;
            // When shutting down notify all the queued calls that they were
            // cancelled due to shutdown.
            if( this._shutting_down ) {                
                for (var i=0, tot=this._queued.length; i < tot; i++) {
                    var rpc = this._queued[i]; 
                    if( rpc.err ) {
                        rpc.err("shutdown");
                    }
                }
            }
        }
    },

    /**
     * Handles timeout events for RPC calls.
     */
    _on_timeout: function (id) {
        if( id in this._active ) {
            var rpc = this._active[id];
            delete this._active[id];
            if( rpc.tmr != null ) {
                clearTimeout(rpc.tmr);
            }
            if( rpc.err ) {
                rpc.err("timeout");
            }
            this.emit(rpc.id + ".timeout", "timeout");
        }
    },

    call: function (name, args, success, error, timeout) {
        if( this._shutting_down == false ) {            
            var id = "_" + "ABCDEFGHIJKLMNOPQRSTUVWXYZ".random(10);
            var timeout_cb = null;
            if( timeout ) {
                var self = this;
                timeout_cb = setTimeout(function () {
                    self._on_timeout(id);
                }, timeout);
            }
            this._queued.push({
                "id": id,
                "call": name,
                "args": args,
                "ok": success,
                "err": error,
                "tmr": timeout_cb
            });
            this._connect();
            this._tick();            
            return id;
        }
    }
});






/*
 .d888888                    
d8'    88                    
88aaaaa88a 88d888b. 88d888b. 
88     88  88'  `88 88'  `88 
88     88  88.  .88 88.  .88 
88     88  88Y888P' 88Y888P' 
           88       88       
           dP       dP      
*/
/**
 * Camaste Core manages the application state on every page.
 */
var Camaste_Core = Stapes.subclass({
    constructor: function () {
        var self = this;
        this._sjs = null;
        this._shutting_down = false;
        this.realtime = new Camaste_Realtime(this);
        $(function(){ self._on_ready(); });
    },

    _on_ready: function () {
        $('html').removeClass('no-js').addClass('js');
    },

    shutdown: function () {
        self._shutting_down = true;
        self.emit('shutdown', self);
    },
});



// ------------------------------------------------------------------------------------------



window.Camaste = new Camaste_Core();

$(function (){
    var do_call = function (self) {
        Camaste.realtime.call("echo", {"derp": 123}, function () {
            setTimeout(function(){
                self(self);
            }, 100);
        });
    };
    do_call(do_call);
});