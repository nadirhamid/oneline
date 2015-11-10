// Frontend of Oneline.  // Written by Nadir Hamid // // Code can be distributed; copied under
// an MIT license
(function () {
  var root = this;
  var Oneline;

  if (typeof exports !== 'undefined')
    Oneline = window.Oneline || {};
  else
    Oneline = root.Oneline = window.Oneline || {};

  // Set some base math functions to the global
  // namespace
  min = Math.min, max = Math.max, pow = Math.pow, sqrt = Math.sqrt, log = Math.log, floor = Math.floor;

  // Do the same for array methods
  slice = Array.slice, splice = Array.splice, every = Array.every;

  /* websocket is needed for every object
   * @class
   */
  websocket = {};

  /* for the geolocation object
   * @class
   */
  navigator = window.navigator ? window.navigator : [];

  window.BSON = window.BSON || bson().BSON;

  /* convinience for BSON -- it will delegate to JSON
   * when needed.
   */
  BSON.stringify = function(packet) { return O.uint8ToString(BSON.serialize(packet)); };
  BSON.parse = function(message) { return BSON.deserialize(O.stringToUint8(message)); };

  Oneline.interop = BSON;
  Oneline.socket = Oneline.socket || [];
  Oneline.settings = Oneline.settings || {};
  Oneline.freq = Oneline.freq = Oneline.freq || 1000;
  Oneline.host = Oneline.host || 'localhost';
  Oneline.port = Oneline.port || 9000;
  Oneline.protoline = Oneline.protoline || [];
  Oneline.objects = Oneline.objects || [];
  Oneline.after = Date.now();
  Oneline.signature = "";
  Oneline.running = 0;
  Oneline.update = 0;
  //  list of async data + keys
  Oneline.asyncs = {};
  // list of async callbacks. Preserve even when invoked
  Oneline.asyncCallbacks = {};
  Oneline.readyIntervalFreq = 100;  // 100ms

  /**
   * accept after a given time
   * all requests will either fail
   * or succeed based on this time.
   *by default this should be the time oneline was initialized
   * 
   *
   * request_time < delta = fail
   * otherwise
   * use callback
   *
   * @param time
   * a time to match
   */
  Oneline.acceptAfter = function(time) {
     Oneline.after = time;
     clearInterval(Oneline.t);
     clearTimeout(Oneline.t);
     clearInterval(Oneline.oot);
     clearTimeout(Oneline.oot);
     clearInterval(Oneline.ooot);
     clearTimeout(Oneline.ooot); 

  };
  Oneline.setAsync = function(key, data, fn) {
     var currentAsyncs = Oneline._getAsyncs();
     var foundAsync=0;
     Oneline.asyncCallbacks[key]=fn;
     for (var i in  currentAsyncs) {
        if (currentAsyncs[i].key===key) {
          // reset to initiated
          currentAsyncs[i].state = 1;
          foundAsync=1;
        }
     }
    if(!foundAsync) {
      // on by default
      currentAsyncs[key]  = { "data": data, state: 1 };
    }
    Oneline.asyncs = currentAsyncs;
  };

  Oneline._getAsyncs = function() {
      return Oneline.asyncs;
  };
  Oneline._getActiveAsyncs = function() {
     var initial = Oneline._getAsyncs();
      var full =initial;
     for (var i in initial) {
        if (initial[i].state===1) {
         // good
        } else {
           delete  full[i];
        }
      }
      //return Oneline._collectAsyncNames(full);
      return Object.keys(full);
    };
  Oneline._collectAsyncNames = function(listOfAsyncs) {
      var names = [];
      for (var i in listOfAsyncs) {
          names.push(i);
      }
      return names;
    }; 
  Oneline.callAsync = function(asyncName) {
    var theAsync = Oneline.getAsync(asyncName);
    if (theAsync) {
      Oneline.asyncCallbacks[asyncName](theAsync);
    }
  };

  Oneline.getAsync = function(key) {
     if (typeof Oneline.asyncs[key] !== 'undefined'  && Oneline.asyncs[key].state === 1) {
         Oneline.asyncs[key].state=0; 
         return Oneline.asyncs[key].data;
      }
      return false;
  };

  Oneline.newSignature = function() {
    Oneline.signature = Oneline.uuid();
  };
  Oneline.allReady = function() {
    var countOfObjects = Oneline.objects.length;
    var countReady = 0;
    for (  var  i  in Oneline.objects ) {
        if (Oneline.objects[i].state === 1 ) {
          countReady ++;
        }
     }
     return countReady === countOfObjects - 1  ? true : false;      
  };

  Oneline.collectAll = function() {
    var packet = {};
    for (var i in Oneline.objects) {
       packet[Oneline.objects[i].type] = Oneline.objects[i].m;
    }
    return packet;
   };
  Oneline.joinOrNew =  function(obj) {
     var needsMerge = 0;
     Oneline.signature = Oneline.uuid();
     for (var i in Oneline.objects) {
        if (Oneline.objects[i].type === obj.type) {
            delete Oneline.objects[i]; 
            Oneline.objects[i] = obj;
            Oneline.objects[i].state = 0; 
            Oneline.update = 1;
            needsMerge = 1;
         }
      }
      if (!needsMerge) {
          Oneline.objects.push(obj);
      }
    };
               
  // one time
  Oneline.once =   function(event_type, message) {
           var m_ = {}; 
           var packet = {};        
    

            if (typeof event_type === "object") {
              packet[event_type.obj]  = {};
              packet[event_type.obj]['type']  =  event_type.data.type;
              packet[event_type.obj]['data'] = event_type.data.data;
            } else {
            message['type'] =  event_type;
            message['data'] = {};
            // TODO no backwards captability should be present, in next version
            for(var i in Object.keys(message)) {
            message['data'][message[i]] = message[i];
            delete message[i];
            }
           }
            packet["generic"]  = message;

                          t = Date.now();
                          m_.packet = packet; 
                          m_.packet.order = [];
                          m_.packet.interop = O.interop;
                          m_.uuid = O.uuid();
                          m_.timestamp = t;
                          m_.connection_uuid = O.connection_uuid;
        // wait for callback
        // and the connection
        Oneline.socket.send(Oneline.interop.stringify(m_));
  };

  Oneline.alwaysConnect  = function()  {  // always listen for the server, evenm when disconnected
      Oneline.alwaysConnectInterval = setInterval(function() {
            if (Oneline.socket.readyState ===2  || Oneline.socket.readyState === 3) {
                Oneline.connector.connect();
            } else { // wait
            }
      }, 0);
   };
  Oneline.ready = function(callback) {
      var readyInterval= setInterval(function() {
          if (Oneline.socket.readyState === 1) {
            callback();
            clearInterval(readyInterval);
          } else {
            // try to reconnect
            
           Oneline.connector.connect();
          }
      }, Oneline.readyIntervalFreq);
  };

  Oneline.clearCurrent = function(instance) {
    for (var i in Oneline.objects) { if (Oneline.objects[i] instanceof instance) {
          delete Oneline.objects[i];
        }
    }
  };

  /**
   * get the after parameter of  
   * oneline
   */
  Oneline.getAfter = function() {
      return Oneline.after;
   };
    

  /* setup online with the 
   * given options.
   *
   * @param options -> object
   */
  Oneline.setup = function(options, signature) {
      Oneline.settings = options;
      Oneline.port = options.port || Oneline.port;
      Oneline.host = options.host || Oneline.host; Oneline.type = options.type === 'bind' ? 'bind' : 'auto';
      Oneline.on = options.on || 'click';
      Oneline.target = options.target;
      Oneline.signalStop = false;
      Oneline.connection_uuid = Oneline.connection_uuid || Oneline.uuid();
      if (typeof signature === 'undefined') {
      Oneline.signature = Oneline.uuid();
      }
      options.server = options.module || options.server;
    
      Oneline.settings.alwaysConnect  = typeof Oneline.settings.alwaysConnect === 'undefined'  ? false  : (Oneline.settings.alwaysConnect ? true : false);
      if (options.server.match(/ws\:\/\//))
        Oneline.settings.server = options.server;
      else
        Oneline.settings.server = options.server = 'ws://' + Oneline.host + ':' + Oneline.port + '/' + options.server;

      if (OnelineTransport.WebSockets.detect()) {
      Oneline.socket = OnelineTransport.WebSockets.Ctor(Oneline.settings.server);
      } else {
      //  fallback
      // to xhr
        if (OnelineTransport.XHR.detect()) {
          Oneline.settings.xhrurl = "http://" + Oneline.host + ":" + ((parseInt(Oneline.port) + 1)).toString();
          Oneline.socket = OnelineTransport.XHR.Ctor(Oneline.settings.xhrurl, Oneline.settings.server);
          Oneline.loaded = true;
        } else {
          // todo other transportation
          console.log("Neither XHR or WebSocket transport is available in this browser");
        }
      }
      Oneline.interop = typeof options.interop !== 'undefined' ? options.interop === 'json' ? JSON : BSON : BSON;
      Oneline.freq = typeof options.freq !== 'undefined' ? options.freq : Oneline.freq;
      Oneline.socket.onopen = function() { };
      Oneline.socket.onmessage = function(evt) { 
          var data =  Oneline.interop.parse(evt.data);

          //if (parseInt(data.timestamp_request) >  parseInt(Oneline.getAfter())) {
              var collectedAsyncs = [];

              // call all the asyncs
              for (var i in data.asyncs) {
                  Oneline.callAsync(data.asyncs[i]);
              }
              if (typeof Oneline.callback  === 'function') {
              Oneline.callback(data);
              }
         // }
       };
      //Oneline.connector.connect();
      if (typeof options.order !== 'undefined') {
        Oneline.order = options.order;
      } else {
        Oneline.order = [];
      }

      /* onclose try to reestablish
       * the connection
       */

       /* get a target element 
        * for the target event
        */
      Oneline.target = document.getElementById(Oneline.target);
     // connect the websocket instance
      // moved from pipeline as we may somtimes need to issue messages before
      // the pipeline

     Oneline.connector.connect();
  };

  /**
   * A list of context based options
   * this is for when we don't
   * get user input we will need
   * to resort to their defaults
   * this should have settings foreach
   * object
   *
   * TODO: currently we need to support 
   * all objects in this however every option
   * does not have a default yet
   */
  Oneline.contextOptions = {
     "geolocation": {
        "lat_field": {
            "default": "lat"
        },
        "lng_field": {
            "default": "lng"
        },
        "every":  {
          "default": 10.00
        },
        "limit": {
          "default": 512
        },
        "range": {
          "default": 40.00
        },
        "bidirectional": {
          "default": false
        }
     },
     "time": {
        "sfield": {
          "default": "stime"
        },
        "efield": {
          "default": "etime"
        }
      }
  };
  /**
   * fetch an optional
   * thing when we don't receive it
   * return 0, when we have it 
   * check our lookup array and do 
   * something
   * 
   * @param module:  module to look in
   * @param option: specified option
   * 
   * @method
   */
  Oneline.fetchOptional = function(mod, option, value) {
     if (typeof value === 'undefined') {
        return Oneline.contextOptions[mod][option]['default'];
     }

     return value;
  };
  /**
   is the sender the person who requested this
   stream ?
   * @param response
   *  optional response for the check
  */
  Oneline.isMe = function(response) {
      if (response) {
          if (typeof response.connection_uuid !=='undefined') {
              if (Oneline.connection_uuid === response.connection_uuid) {
                return true;

              }
          }
          if (typeof response === 'string') {
              if (Oneline.connection_uuid === response) {
                return true;
              }
          }
       }
       if (Oneline.lastResponse) {
          if (Oneline.lastResponse.connection_uuid === Oneline.connection_uuid) {
            return true;
          }
      }
      return false;
  };
  /* agent object for oneline
   * @class
   */
  Oneline.agent = function(options) { };

  /* nodes object
   * @class
   */
  Oneline.nodes = function(options) {
  };

  Oneline.stream = function(options) {
    options = options || {};
    options.pipeline = options.pipeline || O.protoline;

    return O.pipeline({}, options.pipeline, function(res) {  } ).run(); 
  };

  /* simple class for 
   * values with operands
   * @class
   */
  Oneline.value = function(op, val) {
      return { 'op': op, 'value': val };
  };

  /* get an elapse
   * of time and convert it 
   * to an integer
   * @class
   */
  Oneline.moment = function(start, end) {
      return { 'start': 0000, 'end': 3600 };
  };

  /** simple echo module
   * output all data in desired db table
   */
  Oneline.echo = Oneline.echo = function(options, ready) {
    Oneline.echo.options = options;
    if (!ready) {
    var obj  = clone(Oneline.echo(options,1));
    obj.signature = Oneline.signature;
    Oneline.joinOrNew(obj);
    }
        
    
    return {
        /**
         * run the echo object
         * this will only look
         * at the table do nothing else
         */
        run: function(m) {
            this.m = m || {};
            this.m.echo = {};
            this.m.echo.limit = O.echo.options.limit;
            this.state = 1;
        }
    }
  };

  /* geolocation module
   * @class
   */
  Oneline.geolocation = Oneline.geo = function(options, ready) {
      Oneline.geolocation.options = options;
      if (!ready) {
      var obj =   clone(Oneline.geolocation(options,1));
      obj.type = "geolocation";
      obj.signature = Oneline.signature;
      obj.options = Oneline.geolocation.options;
      Oneline.joinOrNew(obj);
      }

      return {

          /* run the geolocation object
           * this will call the browsers native 
           * geolocation api or 'navigator'
           * 
           * @param m -> pipeline passed message
           */
          run: function(m) 
          {
              if ( this.state != 1) {
              this.m = m || {};
              this.m.geo = {};
              this.m.geo.every = O.fetchOptional("geolocation", "every", O.geolocation.options.every);
              this.m.geo.range = O.fetchOptional("geolocation", "range", O.geolocation.options.range);
              this.m.geo.limit = O.fetchOptional("geolocation", "limit", O.geolocation.options.limit);
              this.m.geo.lat_field = O.fetchOptional("geolocation","lat_field", O.geolocation.options.lat_field);
              this.m.geo.lng_field = O.fetchOptional("geolocation", "lng_field", O.geolocation.options.lng_field);
              var that = this;
              navigator.geolocation.getCurrentPosition(function(res) {
                  if(res.coords && typeof res.coords !==  'undefined') {
                      that.m.geo.lat =  res.coords.latitude;
                      that.m.geo.lng =  res.coords.longitude;
                      that.state = 1;
                    }
                  });
              }
          }
      };
  };

  /* event module
   * @class
   */
  Oneline.event = function(options, ready) {
      Oneline.event.options = options;
      if (!ready) {
        var obj = clone(Oneline.event(options,1));
        obj.type = "event";
        obj.signature = Oneline.signature;
        obj.options =  Oneline.event.options;
        Oneline.joinOrNew(obj);
      }
      return {

          /* event object does not
           * use any asynchronous functions
           * as a result we should be fine setting state to 1 immediately
           */
          run: function(m) 
          {
              this.m = m || {};
              this.m.event = Oneline.event.options;

              this.state = 1;
          }     
      }
  };


  /**
   * oneline generic
   * class. These just
   * tell oneline to not use oneline
   * pipelining and stick to the module's
   * code.
   * @class
   */
  Oneline.generic = function(options, ready) {
    Oneline.generic.options = options;

    if (!ready) {
     
      var obj = clone(Oneline.generic(options,1));
      obj.type = "generic";
      obj.signature = Oneline.signature;
      obj.options = Oneline.generic.options;
      Oneline.joinOrNew(obj);
    }

      return {

        /**
         * run the generic. These just provide
         * two parameters: type
         * that will tell what needs to be done
         * and data:
         * other stuff
         *
         * Oneline.generic({
              'type': 'call' 
           });
         * Oneline.generic({
              'type': 'do_something'
              'data': []
           });
         */
        run: function(m) 
        {
          this.m = m || {};
          this.m.generic = {};
          this.m.generic.type = Oneline.generic.options.type;
          this.m.generic.data = Oneline.generic.options.data;
          this.state = 1;

          //console.log(this);
        }
      }
  };


  /* time module
   * @class
   */
   Oneline.time = function(options, ready) {
      Oneline.time.options = options;
      
      if (!ready) {
        var obj = clone(Oneline.time(options,1));
        obj.type = "time";
        obj.signature = Oneline.signature;
        obj.options = Oneline.time.options;
        Oneline.joinOrNew(obj);
      }

      return {

          run: function(m)
          {
              this.m = m || {};
              this.m.time = {};              

              if(typeof Oneline.time.options.start !== 'undefined') {
                 this.m.time.start = Oneline.time.options.moment.start;
                 this.m.time.end = Oneline.time.options.moment.end;
              } else if (typeof Oneline.time.options.moment !== 'undefined') {
                this.m.time.start = Oneline.time.options.moment.start;
                this.m.time.end = Oneline.time.options.moment.end;
              }
              this.m.time.sfield = Oneline.fetchOptional("time", "sfield", Oneline.time.options.sfield);
              this.m.time.efield = Oneline.fetchOptional("time", "efield", Oneline.time.options.efield);
              this.state = 1;
          }
      };
   };

   /* random module
    * @class
    */
   Oneline.random = function(options, ready) {
      Oneline.random.options = options;
      if (!ready) { 
        var obj = clone(Oneline.random(options,1));
        obj.type = "random";
        obj.signature = Oneline.signature;
        obj.options = Oneline.random.options;
        Oneline.joinOrNew(obj);
      }

      return {
          run: function(m) 
          {
              this.m = m || {};
              this.m.random = {};

              this.m.random.amount = Oneline.random.options.amount;

              this.state = 1;
          }
      };
   };

  /* pipeline module
   * @class
   */
  Oneline.pipeline = function(agent, objects, callback) {
      if (typeof agent !== 'undefined' && typeof agent !== 'function')
        O.agent = agent;
      else
        O.agent = {};
      if (typeof objects !== 'undefined' && typeof objects !== 'function')
        O.objects = objects;


      
      O.callback = arguments[arguments.length - 1];

      O.protoline.push(this);
      O.linetype = Oneline.type;
      O.provider = O.linetype === 'bind' ? 'Timeout' : 'Interval';
      O.runner = 'Interval';

      return {

          /* stop the oneline streaming
           * this should gracefully shut down
           * the module handler being used as well as clear
           * the client side temp data
           */
          stop: function()
          {
              return O.signalStop = 1;
          },

          /* run the pipeline
           * get messages for all the objects
           * when this is done
           * pass the message to the websocket
           */
          run: function() 
          {
              Oneline.signalStop  = false;
              Oneline.update = 0;
              Oneline.connector.connect();
              this.runtimeSignature = Oneline.signature; 
              var runtimeObject = this; 
              O.t = window['set' + O.provider](function() {
                  if (Oneline.update) {
                     Oneline.running=0;
                     O.connector.clear();
                     O.newSignature(); 
                     return O.pipeline(O.agent,O.objects,O.callback).run();
                  }
                  if (Oneline.running || runtimeObject.runtimeSignature !== O.signature) {
                     return;
                  }
                  if (Oneline.signalStop
                     || O.socket.readyState === 2
                     || O.socket.readyState === 3) {
                      return O.connector.disconnect();
                  }
                  O.running = 1;
                   
                  var m = {}, c = 0, m_ = {}, ii = 0, t, i = 0;

                  /* this should be communative
                   * and not
                   */
                  if (O.objects.length > 1) {
                    for (var i in O.objects) {
                        O.objects[parseInt(i)].run(m);
                 
                         
                        O.oot = window['set' + O.runner](function() {
                            /* check if the prev
                             */ 
                            if (c !== 0 && O.objects[c - 1].state !== 1)
                                return;

                            if (typeof O.objects[c] !== 'object')
                                return;

                            if (O.objects[c].state === 1) {

                                m = collect(m, O.objects[c].m);

                                c ++;

                                window['clear' + O.runner](O.oot);
                            }

                        }, 1);
                    }
                  } else {
                    if (typeof O.objects[0] !== 'undefined' &&  O.objects[0].state === 1) {
                        m = collect(m, O.objects[0].m);
                        c++;
                        window['clear' + O.runner](O.oot);
                    }
                  }

                  O.ooot = window['set' + O.runner](function() {
                      if (c === O.objects.length) {

                          m_.packet = m;

                          /* if we have an agent,
                           * add it to the message
                           */
                          t = new Date().getTime();
                          m_.timestamp = t; 
                          m_.uuid = O.uuid();
                          m_.connection_uuid = O.connection_uuid;
                          if(t >  Oneline.after) {
                          O.socket.send(O.interop.stringify(m_));
                          }
                          O.running = 0;
                         window['clear' + O.runner](O.ooot);
                      }
                  }, 1);

              }, O.freq);
          }
      };
  };

   /* upcoming snapshot
    * allow for event based
    * voice input
    *
    * @class
    */
   Oneline.sound = function(options, ready) {
      Oneline.sound.options = options;
      if (!ready) {
          var obj = clone(Oneline.sound(options,1));
          obj.signature = Oneline.signature;
          obj.type = "sound";
          obj.options = Oneline.sound.options;
          Oneline.joinOrNew(obj);
      }
       
      

      return {
          run: function(m)
          {
              this.m = m || {};
              this.m.sound = {};
              this.m.sound.length = Oneline.sound.options.length || 60;
              this.m.sound.field = Oneline.sound.options.field;
              var that = this;

              Oneline.speech = new webkitSpeechRecognition();

              Oneline.speech.onstart = function() {
              };
              Oneline.speech.onresult = function(e) {
                  console.log(e);
                  that.state = 1;
              };

              Oneline.speech.lang = Oneline.sound.options.lang || "en-GB";
              Oneline.speech.start();
          }
      };
   };


  Oneline.connector =
  {
      /* try to connect
       * to a socket with the initialized
       * settings
       */
      connect: function()
      {
          /* if already trying to connect
           * disregard request
           */
          if (O.socket.readyState === 0 || O.socket.readyState === 1)
            return;

          return O.setup(O.settings, false);
      },
      /* disconnect from the 
       * socket
       */
      disconnect: function()
      {
          if (O.socket.readyState === 2 || O.socket.readyState === 3)
            return;

          O.connector.clear();
          return O.socket.close();
      },
      clear: function() {
          window['clear' + O.provider](O.t);
          window['clear' + O.runner](O.oot);
          window['clear' + O.runner](O.ooot);
      }
  };

  /* generate a uid not more than
   * 1, 000, 000. This code was 'borrowed' from 'KennyTM'
   * @ http://stackoverflow.com/questions/624*666/how-to-generate-short-uid-like-ax4j9z-in-js
   */
  Oneline.uuid = function() 
  {
      return ("0000" + (Math.random()*Math.pow(36,4) << 0).toString(36)).slice(-4)
  };

  /* convert a uint* array to a string
   * useful for bson interchange
   *
   */
  Oneline.uint8ToString = function(arr)
  {
      var o = "[";

      for (var i in arr)
          o += i == arr.length - 1? arr[i].toString() + "]" : arr[i].toString() + ", ";

      return o;
  };

  /* opposite of uint*tostring
   * this assumes the given string is already
   * in uint* format
   */
  Oneline.stringToUint8 = function(str)
  {
      var ds = str.match(/(\d+)/g), o = [];

      for (var i = 0; i != ds.length; i ++)
        o.push(parseInt(ds[i]));

      return o;
  }; 
 
  /* method borrowed from 'Bjorn' 
   * it will merge object properties into
   * one object 
   */
  function collect(a, b, c) {
    for (property in b)
        a[property] = b[property];

    for (property in c)
        a[property] = c[property];

    return a;
   };

  /* Assign the global object for oneline
   * @shortcut O -> Oneline object
   */
  window.O = window.ol = Oneline;

}).call(this);



/**
 * Deep copy an object (make copies of all its object properties, sub-properties, etc.)
 * An improved version of http://keithdevens.com/weblog/archive/2007/Jun/07/javascript.clone
 * that doesn't break if the constructor has required parameters
 * 
 * It also borrows some code from http://stackoverflow.com/a/11621004/560114
 */ 
function clone(src, /* INTERNAL */ _visited) {
    if(src == null || typeof(src) !== 'object'){
        return src;
    }

    // Initialize the visited objects array if needed
    // This is used to detect cyclic references
    if (_visited == undefined){
        _visited = [];
    }
    // Otherwise, ensure src has not already been visited
    else {
        var i, len = _visited.length;
        for (i = 0; i < len; i++) {
            // If src was already visited, don't try to copy it, just return the reference
            if (src === _visited[i]) {
                return src;
            }
        }
    }

    // Add this object to the visited array
    _visited.push(src);

    //Honor native/custom clone methods
    if(typeof src.clone == 'function'){
        return src.clone(true);
    }

    //Special cases:
    //Array
    if (Object.prototype.toString.call(src) == '[object Array]') {
        //[].slice(0) would soft clone
        ret = src.slice();
        var i = ret.length;
        while (i--){
            ret[i] = clone(ret[i], _visited);
        }
        return ret;
    }
    //Date
    if (src instanceof Date){
        return new Date(src.getTime());
    }
    //RegExp
    if(src instanceof RegExp){
        return new RegExp(src);
    }
    //DOM Elements
    if(src.nodeType && typeof src.cloneNode == 'function'){
        return src.cloneNode(true);
    }

    //If we've reached here, we have a regular object, array, or function

    //make sure the returned object has the same prototype as the original
    var proto = (Object.getPrototypeOf ? Object.getPrototypeOf(src): src.__proto__);
    if (!proto) {
        proto = src.constructor.prototype; //this line would probably only be reached by very old browsers 
    }
    var ret = object_create(proto);

    for(var key in src){
        //Note: this does NOT preserve ES5 property attributes like 'writable', 'enumerable', etc.
        //For an example of how this could be modified to do so, see the singleMixin() function
        ret[key] = clone(src[key], _visited);
    }
    return ret;
}

//If Object.create isn't already defined, we just do the simple shim, without the second argument,
//since that's all we need here
var object_create = Object.create;
if (typeof object_create !== 'function') {
    object_create = function(o) {
        function F() {}
        F.prototype = o;
        return new F();
    };
}

