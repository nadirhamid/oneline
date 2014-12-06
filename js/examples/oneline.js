// Frontend of Oneline.
// Written by Nadir Hamid
//
// Code can be distributed; copied under
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
  Oneline.loaded = 0;

  /* setup online with the 
   * given options.
   *
   * @param options -> object
   */
  Oneline.setup = function(options) {
      Oneline.settings = options;
      Oneline.port = options.port || Oneline.port;
      Oneline.host = options.host || Oneline.host;
      Oneline.type = options.type === 'bind' ? 'bind' : 'auto';
      Oneline.on = options.on || 'click';
      Oneline.target = options.target;

      options.server = options.module || options.server;

      if (options.server.match(/ws\:\/\//))
        Oneline.settings.server = options.server;
      else
        Oneline.settings.server = options.server = 'ws://' + Oneline.host + ':' + Oneline.port + '/' + options.server;

      Oneline.socket = window.WebSocket ? new window.WebSocket(options.server) : MozWebSocket(options.server); 
      Oneline.interop = typeof options.interop !== 'undefined' ? options.interop === 'json' ? JSON : BSON : BSON;
      Oneline.freq = typeof options.freq !== 'undefined' ? options.freq : Oneline.freq;
      Oneline.socket.onopen = function() { Oneline.loaded = 1; };       
      Oneline.socket.onmessage = function(evt) { console.log(O.interop.parse(evt.data)); };

      /* onclose try to reestablish
       * the connection
       */

       /* get a target element 
        * for the target event
        */
      Oneline.target = document.getElementById(Oneline.target);

      console.log(Oneline.target);
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

    return O.pipeline({}, options.pipeline, function(res) { console.log(res); } ).run(); 
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

  /* geolocation module
   * @class
   */
  Oneline.geolocation = Oneline.geo = function(options) {
      Oneline.geolocation.options = options;

      return {

          /* run the geolocation object
           * this will call the browsers native 
           * geolocation api or 'navigator'
           * 
           * @param m -> pipeline passed message
           */
          run: function(m) 
          {
              this.m = m || {};
              this.m.geo = {};
              this.state = 0;
              this.m.geo.every = O.geolocation.options.every;
              this.m.geo.range = O.geolocation.options.range;
              var that = this;

              navigator.geolocation.getCurrentPosition(function(res) {
                  that.m.geo.lat = res.coords.longitude;
                  that.m.geo.lng = res.coords.latitude;
                  that.m.geo.range = O.geolocation.options.range;
                  that.state = 1;
              });
          }
      };
  };

  /* event module
   * @class
   */
  Oneline.event = function(options) {
      Oneline.event.options = options;

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


  /* time module
   * @class
   */
   Oneline.time = function(options) {
      Oneline.time.options = options;

      return {

          run: function(m)
          {
              this.m = m || {};
              this.m.time = {};              

              this.m.time.start = Oneline.time.options.moment.start;
              this.m.time.end = Oneline.time.options.moment.end;

              this.state = 1;
          }
      };
   };

   /* random module
    * @class
    */
   Oneline.random = function(options) {
      Oneline.random.options = options;

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
      O.objects = objects;
      O.callback = callback;
      O.protoline.push(this);
      O.linetype = Oneline.type;
      O.provider = O.linetype === 'bind' ? 'Timeout' : 'Interval';
      O.runner = 'Interval';

      if (Oneline.type === 'bind')
          if (typeof Oneline.target !== 'undefined' && Oneline.target.tagName)
                Oneline.target['on' + Oneline.on] = 
                   function() { return Oneline.pipeline(agent, O.objects, O.callback).run(); }

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
              O.t = window['set' + O.provider](function() {
                  if (Oneline.running)
                      return;

                  if (!Oneline.loaded)
                      return O.connector.connect();

                  if (Oneline.signalStop
                     || O.socket.readyState === 2
                     || O.socket.readyState === 3) {
                      return O.connector.disconnect();
                  }

                  O.running = 1;
                  O.socket.onmessage = function(evt) { return O.callback(O.interop.parse(evt.data)); };

                  var m = {}, c = 0, m_ = {}, ii = 0, t, i = 0;

                  /* this should be communative
                   * and not
                   */
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

                  O.ooot = window['set' + O.runner](function() {
                      if (c === O.objects.length) {
                          m_.packet = m;

                          /* if we have an agent,
                           * add it to the message
                           */
                          t = new Date().getTime();
                          m_.packet.timestamp = t; 
                          m_.packet.interop = O.interop;
                          m_.uuid = O.uuid();

                          O.socket.send(O.interop.stringify(m_));

                          if (typeof O.callback === 'function')
                              O.callback(m_);

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
   Oneline.sound = function(options) {
      Oneline.sound.options = options;

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
          if (O.socket.readyState === 0)
            return;

          return O.setup(O.settings);
      },
      /* disconnect from the 
       * socket
       */
      disconnect: function()
      {
          O.loaded = 0;

          if (O.socket.readyState === 3)
            return;

          return O.socket.close();
      }
  };

  /* generate a uid not more than
   * 1, 000, 000. This code was 'borrowed' from 'KennyTM'
   * @ http://stackoverflow.com/questions/6248666/how-to-generate-short-uid-like-ax4j9z-in-js
   */
  Oneline.uuid = function() 
  {
      return ("0000" + (Math.random()*Math.pow(36,4) << 0).toString(36)).slice(-4)
  };

  /* convert a uint8 array to a string
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

  /* opposite of uint8tostring
   * this assumes the given string is already
   * in uint8 format
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