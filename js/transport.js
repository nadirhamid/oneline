// suite of transportation
// options for oneline
//
// should support the following:
// WebSockets (native)
// XHR (needs XHR server)
// XDR * coming soon
// iFrame * coming soon

// each transport should
// provide similar functions
//
// usage:
// var transport = OnelineTransport.WebSocket
// var transport = OnelineTransport.XHR
(function() {
  var root = this;
  var OnelineTransport;
    
  if (typeof exports !== 'undefined')
    OnelineTransport = window.OnelineTransport || {};
  else
    OnelineTransport = root.OnelineTransport = window.OnelineTransport || {};

  OnelineTransport.WebSockets = {}; 
  Oneline = window.Oneline || {};

  OnelineTransport.WebSockets.Ctor = function(settings) {
     return window.WebSocket? new window.WebSocket(settings) : new window.MozWebSocket(settings);
  };
  OnelineTransport.WebSockets.detect = function() {
    if (window.WebSocket) {
      return true;
    }
    // when we have
    // no window.websocket
    // we can still have
    // mozwebsocket
    if (window.MozWebSocket) {
      return true;
    } 
  
    return false;
  };


  OnelineTransport.XHR =  {};
  OnelineTransport.XHR.key = null;
  OnelineTransport.XHR.Ctor = function(xhrurl, modurl) {
    // a key used to maintain our session
    if (!OnelineTransport.XHR.key) {
      OnelineTransport.XHR.key = Oneline.uuid();
    }
    return OnelineTransport.XHR.reform(xhrurl, modurl);
  };
  OnelineTransport.XHR.opened = false;
  OnelineTransport.XHR.reform = function(xhrurl, modurl) {
    OnelineTransport.XHR.dataPost = "modUrl=" + modurl;
    var xhr = new XMLHttpRequest();
    // hack transport our settings with
    // xhr we need the same websockets url
    var modurl = Oneline.settings.server;
    xhr.open("POST", xhrurl,true);
    xhr.readyState = 0;
    xhr.close = OnelineTransport.XHR.close;
    xhr.sendProto = xhr.send;
    xhr.send = OnelineTransport.XHR.send;
    xhr.onmessage = OnelineTransport.XHR.onmessage;
    xhr.setRequestHeader('Content-type', 'application/x-www-form-urlencoded');  
    xhr.setRequestHeader("X-XHR-Websockets-Oneline", true);

    return xhr;
  };
  OnelineTransport.XHR.close = function() {
      // stub
  };

  OnelineTransport.XHR.send = function(msg) {
    if (!Oneline.socket.loaded) {
        Oneline.socket = OnelineTransport.XHR.reform(Oneline.settings.xhrurl, Oneline.settings.server);
        Oneline.loaded = false;
    }
    if (!OnelineTransport.XHR.opened) {
        OnelineTransport.XHR.opened = true;
    }
    Oneline.socket.onreadystatechange = function() {
      Oneline.socket.readyState = this.readyState;
      if (this.readyState === 4 && this.code >= 200 && this.code <= 299) {
        // call our on message function
        // should be analagous
        // to a websocket callee
        OnelineTransport.XHR.onmessage({
          "data": this.responseText
        });
      }
    };
    // add our data
    // 
    OnelineTransport.XHR.dataPost += "&data=" + msg + "&key=" + OnelineTransport.XHR.key;
    
    Oneline.socket.sendProto(OnelineTransport.XHR.dataPost);
  };

  OnelineTransport.XHR.onmessage = function(evt) {
      Oneline.socket.onmessage(evt);         
  };
  OnelineTransport.XHR.detect = function() {
    if (window.XMLHttpRequest) {
      return true;
    }
    // TODO XDRRequest is
    // another thing we can resort to
    // other possibilities include:
    // jsonp
    // iframe
    // ..
    return false;
  };

}).call(this);
