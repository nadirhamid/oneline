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

  Oneline.socket = Oneline.socket || [];
  Oneline.settings = Oneline.settings || {};
  Oneline.freq = Oneline.freq = Oneline.freq || 1000;
  Oneline.loaded = 0;

  /* setup online with the 
   * given options.
   *
   * @param options -> object
   */
  Oneline.setup = function(options) {
      Oneline.settings = options;
      Oneline.socket = window.WebSocket ? new window.WebSocket(options.server) : MozWebSocket(options.server); 
      Oneline.freq = typeof options.freq !== 'undefined' ? options.freq : Oneline.freq;
      Oneline.socket.onopen = function() { Oneline.loaded = 1; };       
      Oneline.socket.onmessage = function(evt) { console.log(JSON.parse(evt.data)); };

      /* onclose try to reestablish
       * the connection
       */
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

  /* simple class for 
   * values with operands
   * @class
   */
  Oneline.value = function(op, val) {
      return { 'op': op, 'value': val };
  };

  /* geolocation module
   * @class
   */
  Oneline.geolocation = function(options) {
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
              this.m = {};
              this.state = 0;
              this.every = O.geolocation.options.every;
              this.range = O.geolocation.options.range;
              var that = this;

              navigator.geolocation.getCurrentPosition(function(res) {
                  that.m.lat = res.coords.longitude;
                  that.m.lng = res.coords.latitude;
                  that.m.range = O.geolocation.options.range;
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
              this.m = {};
              this.m.event = Oneline.event.options;

              this.state = 1;
          }     
      }
  };

  /* pipeline module
   * @class
   */
  Oneline.pipeline = function(agent, objects, callback) {
      O.objects = objects;
      O.callback = callback;

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
              O.t = setInterval(function() {
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

                  var m = {}, c = 0, m_ = {}, ii = 0, t, i = 0;

                  /* this should be communative
                   * and not
                   */

                  for (var i in O.objects) {
                      O.objects[parseInt(i)].run(m);

                      O.oot = setInterval(function() {

                          /* check if the prev
                           */ 
                          if (c !== 0 && O.objects[c - 1].state !== 1)
                              return;

                          if (typeof O.objects[c] !== 'object')
                              return;

                          if (O.objects[c].state === 1) {

                              m = collect(m, O.objects[c].m);

                              c ++;

                              clearInterval(O.oot);
                          }

                      }, 1);
                  }

                  O.ooot = setInterval(function() {
                      if (c === O.objects.length) {
                          m_.packet = m;

                          /* if we have an agent,
                           * add it to the message
                           */

                          t = new Date().getTime();
                          m_.packet.timestamp = t; 
                          m_.uuid = O.uuid();

                          O.socket.send(JSON.stringify(m_));

                          if (typeof O.callback === 'function')
                              O.callback(m_);

                          O.running = 0;
                          clearInterval(O.ooot);
                      }
                  }, 1);

              }, O.freq);
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
  window.O = Oneline;

}).call(this);