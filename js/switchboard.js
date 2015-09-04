(function() { root  = this; root.switchboard = window.switchboard || {}; switchboard.main_container =  $("#switchboard_container").get()[0]; switchboard.main_box = document.body; switchboard.welcomed =  false; switchboard.no_entry_warned = false; switchboard.applicationName = "Switchboard Application"; switchboard.counter = "00:00:00"; switchboard.members = {}; switchboard.messages = { "global": {} };  

switchboard.devices ={};
switchboard.currentCall =null;
switchboard.inSetup = false;  // called when core is being setup

switchboard.boxerIsWaiting = false;
switchboard.base_url = "http://159.100.186.106/lpc/yii2/framework/web/switchboard/web/"; 
switchboard.currentDevice = null;
switchboard.splashBackgrounds = [
      ""
];

switchboard.warnings = [{
}];

switchboard.systemTimeUnix =0;
switchboard.offsetSystem = -4;


switchboard.deltas = [
    { "delta": 3600, "color": "green" },
    { "delta": 300, "color": "yellow" },
    { "delta": 5, "color": "red" }
];
// update based on server side implementation 

switchboard.prependMessages = false;
 switchboard.settings = {
  "currentlyRecording": "",
  "systemTimezoneOffset": 4,
  "systemTimezoneMinus": true
};

switchboard.callbacks = {
};
switchboard.async = {
};
switchboard.currentSystemTime = 0;


switchboard.mainIntervalOne = null;
switchboard.mainIntervalTwo = null;

switchboard.chattingWith = "global";
switchboard.currentConference = {};
switchboard.currentRecording = {};
switchboard.ajax = {
      "uploadFile": "./?r=profile/upload"
  };



switchboard.synced = false;
switchboard.fields = [{ "type": "recording", "title": "Schedule A Time To Record", "fields": [ 
          {
              "type": "description",
              "id": "recording_time_desc",
              "title": "",
              "value": "The system timezone is EST. Please make sure to schedule the recordings accordingly"
            },
      
        {
            "type": "text",
            "id": "recording_name",
            "title": "Please label this recording session",
            "parentId": "recordingName",
        },
        {
            "type": "textarea",
            "id": "recording_description",
            "title": "Please enter a description for this recording",
            "parentId": "recoridingDescription"
        },
        
        { "type": "date",
              "id": "recordingStartDate",
              "title": "When Would You Like To Record",
              "parentId": "recording_start_date"
        },
        {
              "type":"date",
              "id": "recordingEndDate",
              "title": "When Would You Like To Stop Recording",
              "parentId": "recording_end_date"
        }, {
            "type":"description",
            "id": "main",
            "title": "Notice",
           "value": "",
            "parentId": "recordingDescription"
        }
        ]
    },
      {
          "type": "conference",
          "title":"Create A New Conference",
          "fields": [{
                "title": "Please label this conference",
                "type": "text",
                "id": "conference_title",
                "parentId": "conference_title_parent"
            },
            {
                "title": "Please enter a description for this conference",
                "type": "textarea",
                "id": "conference_description",
                "parentId": "conference_description_parent"
            },
            {
                "title": "Will you record only (host records)",
                "type": "checkbox",
                "id": "host_records",
                "parentId": "conference_host_records_parent"
            },
            {
                "title": "Private Conference", 
                "type": "checkbox",
                "id": "private",
                "callback":"showConferenceMemberList",
                "parentId": "private_conference_parent",
                "when": "click"
            },
            {
                "title": "Conference Member List",
                "type": "list_box",
                "hidden": true,
                "join": true,
                "table":"conference_access_list",
                "async": true,
                "id": "conference_member_list",
                "callback": "getConferenceMembersAndFillPre",
                "parentId": "conference_member_list_parent",
                "when": "right_away" },
              {
                  "title": "conference_id",
                  "id": "id",
                  "type":"hidden"
             } 
        ]
      }


    ];

  switchboard.incomingConnection =null; // global for the call being asked for it can be revoked or accepted depending on  the schedule time
  switchboard.defaults = {
      "chatAway": "",
      "chatOnline": "",
      "chatOffline": "" };

  switchboard.config = {
      "nickname": "",
      "profile_img": "",
      "conferenceId":null,
      "guest": false,
      "conferenceMemberId":null ,
      "retrievedMessages":false
  };

  switchboard.getRecordingURL = function() {

  }; 

  switchboard.validateNumber = function(phonenumber) {
    var m = phonenumber.match(/^\+\d{3}\d{3}\d{4}/);
    return m; 
  }; 

  switchboard.allAlpha = function(nickname) {
      var cnt = 0;
      var it = 0;
      while (it != nickname.length) {
          if (nickname[it].match(/[\w\d\_]+/)) {
              cnt ++;
            }
          it++; 
      }
     return  cnt === nickname.length ? true : false;
  };

  switchboard.validateNickname = function(nickname) {
      var check1 = nickname.length >= 4 && nickname.length < 12 ? true : false;
        var check2 = switchboard.allAlpha(nickname) ?  true : false;
     var error_string = "";
    if (!check1) {
        error_string += "The nickname must be between 6 and 12 characters";
    }
    if (!check2) {
        error_string += "The nickname should only include alphanumerics or underscores";
    }

    return  !check1 || !check2 ? {
          "error": true,
          "error_string": error_string
      }  :  {
          "error": false
      };
  };


  switchboard.getCurrentConferenceNumber = function() {
      return switchboard.currentConferenceNumber;
  };

  switchboard.getCurrentPsuedoNumber = function() {
      return switchboard.currentPsuedoNumber;
  };
  switchboard.getCurrentRecordingNumber = function() {
      return switchboard.currentRecordingNumber;
  };
  

  switchboard.createRecordingURL = function() {

  };



  switchboard.getHourOffset = function() {
      return currentTimezoneOffset();
  };


  switchboard.currentModuleSet = function(moduleName) {
      switchboard.currentModule = moduleName;
  };
  switchboard.currentCallbackSet = function(callback) {
      switchboard.currentCallback = callback;
  };
    

  switchboard.request = function (endpoint,params,type, callback) {
       var xhr = new XMLHttpRequest;
      xhr.open(type,endpoint,true);
       xhr.onreadystatechange = function() {       
          if (this.readyState === 4) {
              var data =  JSON.parse(this.responseText);
              callback(data);
            }
        };

      xhr.setRequestHeader("Content-type", "application/json");
      xhr.send(JSON.stringify(params));
  };

      
  switchboard.supportsSkype = function() {
      // first try ie
      try {
          var object = new ActiveXObject("Skype.Detection");
          return true;
      } catch (e) {
         }
     var mimeCheck = typeof navigator['mimeTypes']['application/x-skype'] !== 'undefined' ? true  : false;
    return mimeCheck;
  };





 

  switchboard.reSync = function() {
        switchboard.synced = false;
        $("#switchboard-contacts-list").html("");
        $("#switchboard-chat-messages").html("");
      $("#switchboard-conference-number").html(switchboard.getCurrentConferenceNumber());
        //$("#switchboard-conference-stream").html(switchboard.getMediaStream());
        if (!switchboard.config.guest) {

        $("#switchboard-conference-stream").attr("href",switchboard.getMediaStream());
          switchboard.initDevice(switchboard.currentDeviceToken); } else {
          $("#switchboard-conference-stream").attr("href", "");
          $( "#switchboard-conference-stream").text("Stream Unavailable");
        }
       
        //switchboard.initDevice(switchboard.currentDeviceToken); 
 
  };



  switchboard.setAsync = function(key,val) {
      switchboard.async[key] = val;
    };
   switchboard.getAsync = function(key) {
      if (typeof switchboard.async[key] !== 'undefined') {
      return switchboard.async[key];
      }
      return false;
    };


  switchboard.hasDevice = function(conferenceNumber) {
      for (var i in switchboard.devices) {
        if (switchboard.devices[i].phone_number ===  conferenceNumber) {
          //disconnect all connections
          switchboard.devices[i].instance.disconnectAll();
          return switchboard.devices[i].instance;
      
        }
      }
    return false;
  };
  switchboard.initDevice = function(token) {
      switchboard.currentDevice =  switchboard.hasDevice(switchboard.getCurrentPsuedoNumber());
      if (!switchboard.currentDevice) {
      switchboard.currentDevice= Twilio.Device.setup(token, {"debug": true, "rtc": true });
        switchboard.currentDevice.disconnectAll();
        //switchboard.currentDevice.connect({
       //     agent: switchboard.uid(),
            //phone_number: switchboard.getCurrentPsuedoNumber()
       // });

        /*
        switchboard.currentDevice.ready(function(state) {  
            console.log("twilio device is ready");
            console.log("making call to external number");
            switchboard.currentDevice.call(switchboard.currentConferenceNumber,function(connection) {
                // 
                console.log("connected with:" + connection);
              });
        });
        */

        
        switchboard.currentDevice.ready(function() {
          console.log("switchboard device is ready");
          console.log("accepting calls on: "  +switchboard.currentConferenceNumber);

        switchboard.currentDevice.disconnect(function(connection) { console.log("disconnecting");
          console.log(connection);
        });
        switchboard.currentDevice.error(function(connection) {
          console.log("error on connection:");
          console.log(connection);
        });
       switchboard.currentDevice.connect({
            "phone_number": switchboard.getCurrentPsuedoNumber(),
            "agent": switchboard.uid()
        });
       
 
        switchboard.currentDevice.incoming(function(connection) {
          console.log("accepting a call from" );
          console.log(connection);

          switchboard.currentCall= connection;
          //connection.accept();
          connection.reject();
          });

        });
        // add as an device
        //switchboard.devices.

        switchboard.devices[ switchboard.getCurrentPsuedoNumber() ] =   {
                  "instance":  switchboard.currentDevice,
                  "phone_number": switchboard.getCurrentPsuedoNumber()
        };
     }

    };

  switchboard.runCore = function() {
        if (!switchboard.synced) {
          Oneline.generic({
            "type": "core",
            "data": {
                "allMessages": true,
                "allMembers": true,
                "conferenceId": switchboard.config.conferenceId,
                "conferenceMemberId": switchboard.config.conferenceMemberId,
                "chattingWith":switchboard.chattingWith
              }
            });
            switchboard.synced = true;
          } else {
        Oneline.generic({
            "type": "core",
            "data": {
                "conferenceId": switchboard.config.conferenceId,
                "conferenceMemberId": switchboard.config.conferenceMemberId,
                  "chattingWith": switchboard.chattingWith,
                  "updateSince": switchboard.updateSince
              }
          });
          }
    };

  switchboard.getMessages = function(from) {
       Oneline.once({
              "obj": "generic",
              "data": {
              "type": "getMessages",
              "data": {
                  "recipient":from
              } 
            }
        });
    };


  switchboard.sendMessage = function(message) {
         Oneline.acceptAfter(Date.now());
        setTimeout(function() {
        Oneline.once({
            "obj": "generic", 
            "data": {
              "type": "sendMessage",
              "data": {
                  "message": message,
                  "conferenceMemberId": switchboard.config.conferenceMemberId,
                  "conferenceId": switchboard.config.conferenceId,
                  "chattingWith":switchboard.chattingWith
                }
            }
          });
          }, 100);
        //Oneline.acceptAfter(Date.now());
    };
      

  switchboard.warn = function(msg, lvl) {
     lvl = lvl || 'error';
      console.log(msg);
      if (lvl === 'error') {
          $("#switchboardWarning").text(msg);       
          $("#switchboardWarning").css({"color": "#FF0000"});
      } else if (lvl === "success") {
          $("#switchboardWarning").text(msg);
          $("#switchboardWarning").css({"color": "green"});
      }
      $("#switchboardWarning").fadeIn();
      setTimeout(function() {
          $("#switchboardWarning").fadeOut();
      }, 2000);
  };
 
  switchboard.getFieldsAndTitle = function(type) {
      for (var i in switchboard.fields) {
        if (switchboard.fields[i].type === type) {
          return switchboard.fields[i];
        }
      }
    };

    switchboard.myAccount = function(data) {
        var myAccountField = {
              "title": "Your Account",
              "fields": [{
                  "type": "text",
                  "title": "Nickname",
                  "id": "switchboardNickname"
                },
                {
                  "type": "file",
                  "title": "Profile Picture",
                "id": "switchboardPicture"
                }]
        };
       var currentData = {
              "switchboardNickname": switchboard.config.nickname,
              "switchboardPicture": "./uploads/" + switchboard.config.profile_img
          };
       
       switchboard.dialog(myAccountField['title'], myAccountField['fields'], function() {
            var file =  $("#switchboardPicture").get()[0];
          
            if (typeof file.files !== 'undefined' &&  typeof file.files[0] !== 'undefined') { 
                  switchboard.transferFiles(file, function(fileData, fileName) {
                      console.log("uploading:");
                      console.log(fileData);
                      console.log("fileName:");
                      console.log(fileName);
                      switchboard.request(switchboard.ajax.uploadFile, { "profile_ext": fileName, "profile_img":  fileData, "conferenceMemberId": switchboard.config.conferenceMemberId }, "POST", function(data) { 

                          if (data.status === 'ok' ) {
                          
                           var newFileName = data.file_path;
                           var nickname = $("#switchboardNickname").val();
                           Oneline.once({
                              "obj": "generic", 
                              "data": {
                                "type": "updateAccount", 
                                "data": {
                                    "nickname": nickname,
                                    "profileImg": newFileName,
                                    "conferenceMemberId":  switchboard.config.conferenceMemberId 
                                  }
                               }
                              });
                            } else {
                                switchboard.warn("Could not upload new file");
                                Oneline.once({
                                  "obj": "generic",
                                  "data": {
                                    "type": "updateAccount",
                                    "data": {
                                        "nickname": nickname,
                                        "profileImg": false,
                                        "conferenceMemberId": switchboard.config.conferenceMemberId
                                      }}
                                    }
                                  );
                             }
                                
                        });
                                
                  });
            }  else { 
                  var nickname = $("#switchboardNickname").val();
                  Oneline.generic({
                      "type": "updateAccount",
                      "data": {
                          "nickname": nickname,
                          "profileImg": false,
                          "conferenceMemberId":  switchboard.config.conferenceMemberId
                      }
                  });
            }
      
        }, false, {"submit": true, "text": "Update Account"}, currentData);
  };
    

    switchboard.updateUserInfo = function(response) {
        switchboard.config.nickname = response.nickname;
    };

        
     
               
       

    switchboard.transferFiles = function(files, callback) { 
     var fileReader = new FileReader();
      fileReader.callback =  callback;
     fileReader.fileName = files.files[0].name;
      fileReader.onload = function(evt) {
            var pureData = evt.target.result.replace(/.*base64,/, "");
            this.callback(pureData, fileReader.fileName);
      };
      fileReader.readAsDataURL(files.files[0]);
    };
            
    switchboard.stopRecording = function() {
          var stopRecordingDialog = {                   
                    "type": "Stop Recording", 
                    "title": "Stop Recording",
                    "fields": [{
                      "type": "description",
                      "title": "Ending Recording",
                      "parentId": "stopRecordingParent",
                      "value": "This will end your recording, and the next person in line will have the recording rights. You will have to reschedule after leaving. Are you sure?"
                      }]
              };
  
          switchboard.dialog(stopRecordingDialog['title'],stopRecordingDialog['fields'], function() {
                   Oneline.once(
            
                        {
                            "obj":"generic",
                            "data": {
                          "type": "stopRecording",
                          "data": { 
                                "conferenceId":  switchboard.config.conferenceId, 
                                "conferenceMemberId": switchboard.config.conferenceMemberId
                          }
                        }
                  });
          }, false, {"submit":  true, "text": "End Recording" });

    };
    
    switchboard.startRecording = function() {
      var recordingFields = switchboard.getFieldsAndTitle("recording");
     
      var mainNumber =  switchboard.mainNumber;
      recordingFields['fields'][recordingFields['fields'].length - 1]['value'] = "To start your recording session you will need to dial: " + mainNumber + " at your posted date";

      switchboard.dialog(recordingFields['title'], recordingFields['fields'], function() {
              var recordingStart = $("#recordingStartDate").val();
              var recordingEnd = $("#recordingEndDate").val();
              var recordingName = $("#recording_name").val();          
              var recordingDescription = $("#recording_description").val();
    
              if (recordingStart && recordingEnd && recordingName.length > 6 && recordingDescription.length > 30) {
                  var startDateTime = Date.parse($("#recordingStartDate").val());
                  var endDateTime = Date.parse($("#recordingEndDate").val());

                if (startDateTime < endDateTime) {
                    var inUTC = Date.now();
                    //
                    // current time is the localetimezone
                    // translate to utc
                    // then from utc into system
                 
                    var inSystemStart = parseInt((startDateTime) + ((switchboard.config.hoursBehind * 3600) * 1000));
                    var inSystemEnd = parseInt((endDateTime) + ((switchboard.config.hoursBehind * 3600) * 1000));
                    inSystemStart = inSystemStart + ((switchboard.getHourOffset() * 3600) * 1000);
                    inSystemEnd = inSystemEnd + ((switchboard.getHourOffset() * 3600) * 1000);
                    inSystemStart = inSystemStart - ((switchboard.config.hoursBehind * 3600) * 1000); 
                    inSystemEnd = inSystemEnd - ((switchboard.config.hoursBehind * 3600) * 1000);
                    //inSystemStart = inSystemStart + ((switchboard.offsetSystem * 3600) * 1000);
                    //inSystemEnd = inSystemEnd +  ((switchboard.offsetSystem * 3600) * 1000);
                    
                      
                    
                       
                    if (startDateTime < Date.now()) {
                         switchboard.warn("The recording date was below now");
                    } else { 
                      console.log("recording start date will be " + new Date(inSystemStart)); 
                      console.log("recording end date will; be " + new Date(inSystemEnd));
        
                      console.log("starting recording with: ");
                      console.log({
                          "type": "startRecording",
                        "data": {
                            
                            "startOfRecording": inSystemStart/ 1000,
                            "endOfRecording": inSystemEnd / 1000,
                            "recordingName": recordingName,
                            "recordingDescription": recordingDescription,
                            "conferenceId":  switchboard.config.conferenceId,
                            "conferenceMemberId": switchboard.config.conferenceMemberId
                        }
                        });

                      Oneline.once({
                          "obj": "generic",
                          "data": {
                            "type": "startRecording",
                          "data": {
                              
                              "startOfRecording": inSystemStart / 1000,
                              "endOfRecording": inSystemEnd / 1000,
                              "recordingName": recordingName,
                              "recordingDescription": recordingDescription,
                              "conferenceId":  switchboard.config.conferenceId,
                              "conferenceMemberId": switchboard.config.conferenceMemberId
                          }
                        }
                  });
                      Oneline.acceptAfter(Date.now());

                  }
                } else {
                    switchboard.warn("Please make sure the dates are as follows: start date must be behind the end date. And the start date is ahead of now"); 
                } 
              } else {
                switchboard.warn("Please make sure the title is atleast 12 characters and the description is atleast 156");
              }

        }, true, {"submit": true, "text": "Schedule Recording" });
 
  };

  switchboard.switchOddMonth = function(year, month) {
      var monthOffset = 0;
      if (month == 2) {
          return 28;
        }
      if (month % 1 == 0) {
          return 31;
      } else {
          return 30;
      }
    
  }
  switchboard.getTsOfDate = function(time)  {
        // 2015-09-01 01:01:01
        var matches = time.match(/(\d{4})-(\d{2})-(\d{2})\s+?(\d{2}):(\d{2}):(\d{2})/);
        if (matches) {
          var years = parseInt(matches[1]);
          var months = parseInt(matches[2]);
          var days =parseInt(matches[3]);
          var hours = parseInt(matches[4]);
          var minutes = parseInt(matches[5]);
          var seconds = parseInt(matches[6]);
          var secondsInDayThis = 3600 * 24;

          var secondsInYear = (parseInt(years) - 1970) * (365 * secondsInDayThis);
          var secondsInThisMonth = switchboard.switchOddMonth(years,months);
 
          var secondsInMonth = secondsInThisMonth * (3600 * 24);
          var secondsInDay = days * (3600 * 24);
          var secondsInHours =  3600 * hours;
          var secondsInMinutes = 60 * minutes;
      
          return (secondsInYear + secondsInMonth + secondsInDay + secondsInHours + secondsInMinutes + seconds) * 1000;
        } 
    };



  switchboard.timestamp = function(dateobj) {
      var utcOffset = switchboard.getHourOffset();
         
      var time = new Date(switchboard.getTsOfDate(dateobj));

      var hoursAhead = switchboard.config.hoursAhead;
      var hoursBehind = switchboard.config.hoursBehind;

      var offset = hoursAhead > 0 ?  hoursAhead : hoursBehind * -1;
      time = (time.getTime() / 1000) + (offset * 3600);

      return time;
    }; 
 
  switchboard.datetime = function(time) { 
        var newDate = new Date(parseInt(time) *1000);
        return newDate.getYear() +  "-" + newDate.getMonth() + "-" + newDate.getDate() + " " +  newDate.getHours() + ":" + newDate.getMinutes() + ":"  + newDate.getSeconds();     
    };
 


  switchboard.showConferenceMemberList = function() {
      // toggle
      var obj = $("#conference_member_list_parent").get()[0];   
       
      if (obj.style.display === 'block') {
          obj.style.display ='none';
        } else {
          obj.style.display ='block';
      }
  };


  switchboard.getConferenceMembersAndFillPre = function() {

              var halfASecond = (60 * 1000) / 2;

              //Oneline.acceptAfter(Date.now() + halfASecond);
  
              Oneline.once({
                  "obj": "generic",
                  "data": { 
                  "type": "getAllConferenceMembers",
                  "data": {}
                  }
                });
  };

  switchboard.getField = function(dataset, fieldToGet) {
      var fields = [];
      for (var i in dataset) {
        fields.push(dataset[i][fieldToGet]);
      }
      return fields;
  }; 
  switchboard.getConferenceMembersAndFillPost = function(data) {
          $("#conference_member_list").html("");

        var currentData = switchboard.getAsync("conference_member_list");
        for (var i in data ) {     
            var  li  = $("<li></li>");
            var label = $("<label>" + data[i].nickname + "</label>");
            $(li).attr("class", "conference_member_list_member");
          
            var input = $("<input data-id='" + data[i].id + "' type='checkbox' id='conference_member_" + data[i].id + "'/> ");
            if (currentData) { 
              var currentIds = switchboard.getField(currentData,"conference_member_id");

              if (switchboard.oneOf(data[i].id, currentIds, true)) {
                  $(input).attr("checked", "checked");
              }
            }
      
           $(li).append(label); 
          $(li).append(input);
           $("#conference_member_list").append(li);
        }
        if (typeof switchboard.async['conference_member_list']!=='undefined') {
        delete switchboard.async["conference_member_list"];
        }
  };
      

 

  switchboard.viewConferencesPre = function() {
       
      Oneline.acceptAfter(Date.now());
      
      setTimeout(function() { 
        Oneline.once({
            "obj": "generic",
            "data": {
              "type": "viewConferences",
              "data": {
              } 
            }
        });
        }, 100);
    };
  

switchboard.viewConferencesPost = function(conferences) {
        
        var list =  switchboard.makeList(conferences,['id', 'conference_title','conference_description'], ['hidden', 'text', 'text']); 



        
        var preList = [{
            "type":"button",
            "text": "Create Conference",
            "callback":  "createConferencePre",
            "when":"click"
        }];
        var fullList = preList.concat(list);

    
        var dialog = {
              "type":"View Conferences",
              "title": "View Active Conferences",
              "fields": fullList 
        };
        var options = {
            "showButton": true,
            "buttonText": "Join Conference",
 
            "optionCallback":"switchConference",            
            "optionParams": "id"
        };
 


        switchboard.dialog(dialog['title'],dialog['fields'], function() {}, options, false);
 

    }; 
      

    switchboard.setUpPlayer = function(recording) {
       //var audioBox =  $("<div id='audioBox'></div>");
       var audio =$("<audio style='width:200px;height: 42px;' src='" + recording.recording_url + "'></audio>");
       //$(audio).attr("src", recording.recording_url);  
       
        //switchboard.audioContext.play();
      
        setTimeout(function() { 
        $(audio).mediaelementplayer({ 
            'alwaysShowControls': true,
            'defaultAudioWidth': 600,
            'defaultAudioHeight': 42
          });
        });
       //$("#switchboard-audio-dock").append(audioBox);

       var dialog = {
            "type": "audioPlayer",
            "title": "Playing Recording " + recording.recording_name,
            "fields": [{
               "parentId": "recordingAudioBox",
                "title": "Audio Playback",
                "type": "custom",
                "value": audio
              }]
        }; 
 
        switchboard.dialog(dialog['title'],dialog['fields'], function(){}, false, false, false);
    
    };
    
    switchboard.removePlayer = function() {
          
          $("#audioBox").find("#switchboard-audio-player")[0].player.stop();
          $("#audioBox").remove();
       switchboard.waitForBoxer(function() {});
    };
          
          
 


 
   switchboard.playRecordingPlayer = function(recording) { 
        
        switchboard.tuneOff(function() {
           switchboard.setUpPlayer(recording);
        });
   }; 

 
  // play a recording that is pre recorded
  // this should turn off the live session
  // making this the only thing that is heard
  switchboard.playRecordingPlayerPre = function(recording) {
        
        switchboard.dialog("Are you sure?", [{
              "id": "are_you_sure_recording",
              "title": "",
              "type": "description",
              "value": "By doing this, you will no longer be able to hear the live session."
          }],function() {
            switchboard.waitForBoxer(function() {
              switchboard.playRecordingPlayer(recording);              
              });
          }, false, { "text": "Yes", "submit": true}, false, false);
 
               
  };

   switchboard.playRecording = function(id) {
        switchboard.waitForBoxer(function() {
          Oneline.once({   
                "obj": "generic",
                "data": {
                "type": "getRecordingAndPlay",
                "data": {
                      "recordingId": id
                }
                }
            });
          });
    };
 

       
   switchboard.viewRecordings = function(previous) { 
        Oneline.once({            
              "obj": "generic", 
              "data": {
              "type": previous ?  "viewPreviousRecordings" : "viewUpcomingRecordings", "data": {
                  "conferenceId": switchboard.config.conferenceId
                }
              }
          });
      };

    switchboard.viewUpcomingRecordingsPre = function() {
        switchboard.viewRecordings(false);
    };
    switchboard.viewPreviousRecordingsPre = function() {
        switchboard.viewRecordings(true);
    };
    switchboard.viewRecordingsPre = function() { 
        $(".boxer").not(".retina, .boxer_fixed, boxer_top, .boxer_format, .object").boxer();
        $(".boxer .boxer_fixed").boxer({
             fixed: true 
          });
        $(".boxer .boxer_top").boxer({
             "height": "auto",
              "top": "0px !important",
              "position": "relative" 
        });
      var dialog = {     
             "type": "View Recordings",
              "title": "View Recordings",

            "fields": [{
                "type": "selection",
                "title": "",
                "parentId": "viewPreviousRecordingsParent",
                "text": "View Previous Recordings",
                "action": "viewPreviousRecordingsPre"
              },
              {    
                "type": "selection",
                "title": "",
                "parentId": "viewUpcomingRecordingsParent",
                "text": "View Upcoming Recoridngs",
               "action":"viewUpcomingRecordingsPre"
              }
          ]};
        switchboard.dialog(dialog['title'],dialog['fields'], function() {}, false, false);
      }
      
 


       
 

        

 
 
 



  switchboard.makeList = function(data, keys, types) {
      var list = [];
      for (var i in data) {
        var thisValue = {};
        for (var j in keys) {
            thisValue[keys[j]] = {
                  "value": data[i][keys[j]],
                  "type": types[j]
              };
          }
 
  
        list.push({
          "type": "list-item",
          "parentId": "listItemParent",
          "class": "list",
          "id":   data[i].id,
          "values":  thisValue
        });
      }
      
      return list;

  };
  switchboard.viewUpcomingRecordings = function(data) {
                
      var list =  switchboard.makeList(data,  ['id', 'recording_name', 'recording_description'], ['hidden', 'text', 'description']);
      switchboard.dialog("Upcoming Recordings",  list, function() {
              }, false, true); 
  };

   
  // wait until this dom
  // element is taken out from
  // tree
  switchboard.waitForBoxer = function(callback) {
    
        if (!switchboard.boxerIsWaiting) {
          switchboard.boxerIsWaiting = true;
          var  elementToCheck = $("#boxer"); 
          if (elementToCheck.length > 0) {
          $.boxer("close",function() {
              setTimeout(function() { // open timeout
           switchboard.boxerIsWaiting = false;
           callback();
              }, 500);
          });
          } else {
            switchboard.boxerIsWaiting = false;
            callback();
          }
        }
    };
          
                          
   switchboard.isBoxerOpen = function() { 
        var elements  = ['boxer', 'boxer_overlay', 'boxer_content', 'boxer_fixed'];
        var types = ['#', '#', '.', '.'];
        for (var i in elements) {
            if ($(types[i] + elements[i]).length > 0) {
                return true;
            }
          }
        return false;
    };

   
  switchboard.viewPreviousRecordingsPost = function(data) {
      switchboard.currentCallbackSet("viewRecordingsAndPlay"); 
      switchboard.currentModuleSet("viewRecordings");
      var options = {
            "optionCallback": "playRecording",
            "showButton": true,
            "buttonText": "View Recording",
      };
 

      var list = switchboard.makeList(data, ['id', 'recording_name','recording_description'], ['hidden', 'text' , 'description']);
      switchboard.dialog("Recorded Recordings", list, function() {
          }, options, false);
      
  };
  switchboard.viewUpcomingRecordingsPost = function(data) {
        var list = switchboard.makeList(data, ['id', 'recording_name', 'recording_description'], ['hidden', 'text', 'description']);
          switchboard.dialog("Upcoming Recordings",list, function() {
          }, false, false, false);
    };


      
 




   switchboard.createConferencePre = function() {
        switchboard.waitForBoxer(function() {
            return switchboard.createConference(false,true);
        });
  };

  switchboard.manageConferencePre= function() {
    Oneline.once(
          {
              "obj": "generic",
              "data": {
            "type": "viewConferenceAuth",
            "data": {
                "conferenceId": switchboard.config.conferenceId,
                "conferenceMemberId": switchboard.config.conferenceMemberId
            }
          } 
        });
  };

  switchboard.manageConferencePost = function(conference) {
      switchboard.createConference(conference, false);
   };
       


  switchboard.goToConferenceDialog = function() {
      
          switchboard.dialog("You can now join this conference or stay in the current", [{
                "type": "description",
                "title": "Joining New Conference",
                 "parentId": "joinConferenceParent",
                "value": "When you join a new conference all your chat history and, conference data will be updated to the current conference. You can always however come back to this conference",
        }], function() {

              switchboard.waitForBoxer(function() {
              switchboard.switchConference(switchboard.pendingConferenceId); });

        }, false, { "submit": true, "text": "Go to conference" }, false);

  };

  switchboard.switchConference = function(id) {
        Oneline.once(

              {
                  "obj": "generic",
                  "data": {
                "type": "switchConference", "data": {
                    "conferenceMemberId": switchboard.config.conferenceMemberId,
                    "conferenceId": id
                  }
            }
        });
    };


   

  switchboard.createConference = function(currentData, create) { 
      
      var dialog =switchboard.getFieldsAndTitle("conference");
      switchboard.inCreateMode = create;
     currentData = currentData || false;
      create = typeof create === 'undefined' ? true : create;
 
      switchboard.dialog(dialog['title'],dialog['fields'],function() {
                  var conferenceTitle = $("#conference_title").val();
                    // extract textarea contents, be sure to check the event binding which 
                    // always updates the textarea html on keyup
                  var conferenceDesc = $("#conference_description").html();
                  var  conferencePrivate = $("#private").get()[0].checked ? 1 : 0;
                  var conferenceHostRecords = $("#host_records").get()[0].checked ? 1: 0;
                  var conferenceId = $("#id").val() === "" ? false : $("#id").val();
                  var selectedMembersList = [];
                  if (conferencePrivate) {
                      var selectedMembers = $(".conference_member_list_member");
                      
                      $(selectedMembers).each(function() {
                          var isChecked = $(this).find("input[type=checkbox]").get()[0];
                          if(isChecked.checked) {
                              selectedMembersList.push(parseInt($(isChecked).attr("data-id")));
                          }
                        });
                      }
                  Oneline.once({
                          "obj": "generic",
  
                          "data": {
                            "type": (conferenceId ? "manageConference" : "createConference"),
                            "data": {
                                "conferenceMemberId":  switchboard.config.conferenceMemberId,
                                "conferenceId": conferenceId,
                                "conferenceTitle": conferenceTitle,
                                "conferenceDescription": conferenceDesc,
                                "isPrivate": conferencePrivate,
                                "hostRecordsOnly": conferenceHostRecords,
                                "accessList": selectedMembersList
                              }
                          }
                    });

      },  false, {"text": "Create Conference", "submit": true}, currentData);
    };
    




  switchboard.dialog = function(heading, fields, callback, otherOptions, submitButton, currentData) {
      $(".boxer").not(".retina, .boxer_fixed, .boxer_top, .boxer_format, .object").boxer();
      $(".boxer .boxer_fixed").boxer({
          fixed:true
      }); $(".boxer .boxer_top").boxer({
          "top": "-20px",
          "z-index":"1",
          "padding": "0px !important",
          "height": "auto"
      });
       switchboard.callback = callback; 
        if (switchboard.isBoxerOpen()) {
            return;
          }
      var outerContent = $("<div class='inner_content' style='width: 600px; height: 500px;'></div>");
     var content = $("<div class='main-content'></div>");
      var heading = $("<h2>" + heading + "</h2>");
     var list =  $("<ul class='field-boxes'></ul>");
    for (var i in fields) {    
          
          var listItem = $("<li class='field'></li>");         
          var label = $("<label></label><br />");
          $(listItem).attr("id",fields[i].parentId);
          $(label).text(fields[i].title);
          if ( fields[i].type === "text") {
              var  item =$("<input type='text' id='" + fields[i].id + "'/>");

          } else if (fields[i].type === "textarea") {
              var item = $("<textarea id='" + fields[i].id +"'></textarea>");
              $(item).keyup(function() {
                  $(this).html($(this).val());
              });
          } else if (fields[i].type === 'date') { 
             var item = $("<input class='datetimepicker-date' id='" + fields[i].id + "' />");
              $(item).datetimepicker({
    
                format: "Y-m-d H:i:s",
                defaultTime: "00:00:00"
              });

          } else if (fields[i].type === "hidden" ) {
              var item = $("<input type='hidden' id='" + fields[i].id + "' />");
          

          } else  if (fields[i].type === 'custom') {
              var item = fields[i].value;
         
 
          } else if (fields[i].type === "checkbox") {
              var item = $("<input type='checkbox' id='" + fields[i].id + "'  />");
            
               
          } else if (fields[i].type === "file") {
              var item = $("<input type='file' id='" + fields[i].id + "' />");

 
          } else if (fields[i].type === "list_box") {  //  asycn 
 
              var item = $("<div id='" + fields[i].id + "'></div>");
      

          } else if (fields[i].type === "button") {
              if (typeof fields[i].setup  === 'undefined'  || !fields[i].setup) {
              var item = $("<button class='dc_g_button blue'>" + fields[i].value + "</button>");
              $(item).attr("callback", fields[i].callback);
              $(item).text(fields[i].text);
              $(item).click(function() {
                      
                  switchboard.performCallback($(this).attr("callback"));
              });
              } else {
                var item = fields[i].value;
              }

          } else if (fields[i].type === "description") {
     
            var item  = $("<p>" + fields[i].value + "</p>");
                   

          } else if (fields[i].type === "selection" ) { 
            var item = $("<div></div>");
            $(item).css({"margin-right": "10px", "width": "150px", "height": "100px", "border": "1px solid #E3E3E3", "text-align": "center", "float": "left", "background": "#F5F5F5", "cursor": "pointer", "position": "relative"});
            $(item).attr("data-action", fields[i].action);
      
            var text = $("<div class='text'></div>");
            $(text).css({"position": "absolute", "bottom": "10px"});
            $(text).text(fields[i].text);
           $(item).append(text);
            $(item).click(function() {
                  switchboard[$(this).attr("data-action")]();
            });

          } else if (fields[i].type === "list-item") {
                 
                if (Object.keys(fields[i].values).length > 0) { 
                    var item =$("<ul class='list'></ul>");
                     var thisFieldValues =  fields[i].values;
                  for (var j in thisFieldValues) {
                        var thisFieldValue =  thisFieldValues[j];
                   
                        if (thisFieldValue.type === "text") {
                            var innerItem =  $("<li><span>" + thisFieldValue.value + "</span></li>");
   
                        } else if (thisFieldValue.type === "description" ) {
                            var innerItem = $("<li><div class='description'>" + thisFieldValue.value + "</div></li>");
                        } 

                        $(item).append(innerItem);
                      
                    }
                    if (otherOptions) {
                      if (otherOptions.showButton) {
                          var button = $("<button class='onrender-button' data-id='" + thisFieldValues['id'].value + "'>" + otherOptions.buttonText + "</button>");
                          $(button).attr("data-callback", otherOptions.optionCallback);
    
                          $(button).click(function() {
                                 switchboard[$(this).attr("data-callback")]($(this).attr("data-id"));
                          });

                      $(item).append(button);
                        }
                    }
                  }  
          }


          if (typeof fields[i]['when'] !== 'undefined') {
                if (fields[i]['when'] !== 'right_away' ){ 
                  $(item).attr("callback", fields[i]['callback']);
                  $(item).click(function() {                  
                      switchboard[$(this).attr("callback")]();
                 });

                } else {
                   switchboard[$(fields[i]).attr("callback")]();
                }
          }
     
          var showFlag = false; 
          if (currentData) {

             
         
            if (currentData[fields[i].id]) {
                      
       
             if ( typeof fields[i]['when'] !== 'undefined'  && fields[i]['when'] == "right_away") {
                  switchboard.async[fields[i].id] =  currentData[fields[i].id];        
              } else { 
   
                var tagName = $(item).prop("tagName");
                if (tagName  === 'INPUT') {
                  if (fields[i].type === "file") {
                    var img = document.createElement("img");
                    $(img).attr("src",currentData[fields[i].id]);
                    $(img).css({"width": 64, "height": 64});
                    $(img).attr("class", "float-left");
                    $(item).attr("class", "float-left");

                    $(listItem).append(img);
                  } else {
                    var type = $(item).attr("type");
                    if (type === "checkbox") {
                        if (currentData[fields[i].id]) {
                          $(item).attr("checked", "checked");
                            showFlag = true;
                          }
                        } else {
                          $(item).val(currentData[fields[i].id]);
                        }
                      }
                } else {
                      $(item).html(currentData[fields[i].id]);
                      $(item).val(currentData[fields[i].id]);
                }
              } 
            }
          }

          if ((typeof fields[i]['hidden'] !== 'undefined' && fields[i]['hidden']  || fields[i].type === 'hidden') && !showFlag) {
              $(listItem).hide() ;
          } 

          $(listItem).append(label); 
          $(listItem).append(item);
          $(list).append(listItem);
                          
        }
       $(content).append(heading);
      $(content).append(list);

      $(outerContent).append(content);
    $body = $('body'); 

      $("#submitButton").remove();
      

    if (typeof submitButton ===  'object') {
        var button = $("<button class='dc_g_button blue' id='submitButton'>" + "Submit" + "</button>");
        $(button).text(submitButton['text']); 
         
 
        $(button).click(function() {
              callback();
        });
        $(content).append(button);
    }
        

    $.boxer(outerContent);
  };

  switchboard.getMember = function(id) { 
      return switchboard.members[switchboard.currentConference.id][id];
    };

        
  switchboard.readDelta = function(delta) { // is it one of the accepted deltas?
      // more than max?
     var max = switchboard.deltas[0].delta;    
      if (delta > max) {
          return "white";
      }
  
     
     for (var i = 0; i <=  switchboard.deltas.length - 1; i++) {
        if (typeof switchboard.deltas[i +1] === 'undefined' &&  delta <= switchboard.deltas[i].delta) {
              return switchboard.deltas[i].color;
        }
         if (delta <= switchboard.deltas[i].delta && delta > switchboard.deltas[i + 1].delta) {
              return switchboard.deltas[i].color;
          }
      }
    };
  // is the deltaexact or one minus
   switchboard.matchesDelta = function(recordingId, delta)  {
        var deltas =switchboard.deltas;       
        for ( var i in deltas) {  
            if (delta === deltas[i].delta  || delta === deltas[i].delta - 1 || delta === deltas[i]
              && !switchboard.inWarnings(recordingId,delta[i].delta)
              ) {
                  switchboard.warnings.push({
                      "recordingId":recordingId,
                      "delta": delta[i].delta
                    });
                    
                  return true;
              }
          }


        };

    switchboard.inWarnings = function(recordingId, delta){ //membership check did the recording warning get called?
        var warnins = switchboard.warnings;
        for ( var i  in  warnins) {
          if(warnins[i].recordingId === recordingId && delta === warnins[i].delta) {
              return true;
          }
        }
        return false;
    };
 
      
  switchboard.humanizeDelta = function(delta) { 
        var output = { "hours": 0, "seconds": 0, "minutes": 0 };
          var hours= 0, minutes = 0, seconds = 0;
            var counter = delta;

          // counter is 3601 is 
          //  counter -= 3600
         //  coutner  - 1
         // counter  = 
        // hours = 1
        // and minutes and and seconds is 1
                // odd number
              if (counter > 3600) { 
                 var phours =  parseInt(counter / 3600);
                  var rem =  3600 * phours;
                          
                  var mintogo = counter - rem;
                  if (mintogo >= 60) {
                  var pmin = parseInt(mintogo  /  60);
                   var sectogo = pmin * 60;
                  var  psec = mintogo - sectogo;
                  } else {
                   var pmin = 0;
                    var psec =  mintogo;
                  }
                  seconds = psec;
                  minutes = pmin; 
                  hours = phours;

                } else if (counter > 60) {
                  var pminutes = parseInt(counter / 60);
                  var rem = 60 * pminutes;
                  var sectogo = counter - rem;
                  minutes = pminutes;
                  seconds = sectogo;
               } else {
                  seconds = counter;
                  counter = 0;
              }

      output['hours'] = hours.toString().length === 1 ?  "0" + hours.toString() :hours.toString();
      output['minutes'] = minutes.toString().length === 1 ? "0"  + minutes.toString() :  minutes.toString();
      output['seconds'] =seconds.toString().length === 1 ? "0" + seconds.toString() :  seconds.toString();
      return output;
  };

  switchboard.showRecordingButtons = function() {
      $("#stop_recording").show();
      $("#start_recording").hide();
  };

  switchboard.displayUser = function() {
       //Oneline.generic({ 
        //  "type": "getUser",
         // "data": { 
        var thisUser =switchboard.members[id];
       
        var dialog = [{
            "title": "Member: " +thisUser.nickname,
            "fields": [{ 
                "type": "description",
                "title": "Joined On",
                "value": switchboard.humanDateFromTimeStamp(thisUser.joined) 
              } ]
          }]; 
      
  
        switchboard.dialog(dialog);  
      
  };
      

  switchboard.sortMessages = function(messages) {
      var maxTime = 0;     
      var minTime = 0;
      var pos ={}; 

     for (var i  = 0; i <= messages.length ; i ++ )  {
        var parsedI = parseInt(messages[i].message.time);
         for (var j = 0;  j <=messages.length; j ++ ) { 
              var parsedJ = parseInt(messages[j].message.time);
            if (parsedI > parsedJ) {
              pos[j+1] =messages[i];
            } else {
              pos[j] =  messages[i];
            }
        }
      }
     var output = []; 
     var currentNumber = Object.keys(pos).length;
      while (currentNumber <= 0) {
          for (var i in pos) {
              if (parseInt(i) === currentNumber) {
                  output.push(pos[i]);
              }
            }
            currentNumber --;
        }
      return output;
    };
 

  switchboard.showMessages = function(messages) {
       for (var i in messages) { 
            if ($("#message_" + messages[i].message.id).length === 0) {

              var li = document.createElement("li");
              var img = $("<img src='./uploads/" + messages[i].user.profile_img + "' width='30' height='30'/>");
              var username = $("<a class='user-name'>" + messages[i].user.nickname + "</a>");
              $(username).attr("data-id", messages[i].user.id);
              $(username).click(function() {
                  switchboard.displayUser($(this).attr("user-id"));
              });
  
              var bubble = $("<div class='bubble'></div>"); 

              var message = $("<p class='message'>" +messages[i].message.message + "</p>");
              var time = $("<span class='time'><strong>" + switchboard.datetime(messages[i].message.time) + "</strong></span>");
         $(bubble).append(username);
             $(bubble).append(message);
              $(bubble).append(time);
              $(li).append(img);
              $(li).append(bubble);
              $(li).attr("id", "message_"+messages[i].message.id); 
              $(li).attr("class", "message-content");
              $("#switchboard-chat-messages").append(li);
            }
        }
        switchboard.updateMessages(messages);
    };
  switchboard.showMembers = function(users) {
       //console.log(users);
      for (var i in users) {
           
          if ($("#" + users[i].id + "_member").get().length === 0 && users[i].id !== parseInt(switchboard.config.conferenceMemberId)) {
            var li = document.createElement("li");
            $(li).attr("id",users[i].id + "_member"); var a = $("<a class=''>" + users[i].nickname + "</a>");
            var img = $("<img src='./uploads/" + users[i].profile_img + "'></img>");
            if (users[i].status === 'A') {
            var  ico = $("<i class='" + switchboard.defaults.chatAway + "'></i>");
            } else if (users[i].status === 'ON') {
            var ico = $("<i class='" + switchboard.defaults.chatOnline + "'></i>");
            } else if (users[i].status === 'OFF') {
            var ico = $("<i class='" + switchboard.defaults.chatOffline +"'></i>");
            }
            $(li).append(a);
            $(a).append(img);
            $(a).append(ico);
            $(li).attr("data-id", users[i].id);
            $(li).click(function() {

                if (switchboard.chattingWith !==  $(this).attr("data-id")) {
              
       
                    switchboard.chattingWith = parseInt($(this).attr("data-id"));       
                    //Oneline.acceptAfter(Date.now());
                    var lastUpdate = switchboard.getLastMessageFrom();
                   
                    if (!lastUpdate) { 
                    switchboard.synced =false;
                    switchboard.prependMessages = false;
                    } else {
                    switchboard.prependMessages = true;
                    switchboard.updateSince =lastUpdate.time;
                    }
                    $("#switchboard-chat-messages").html(""); 
                }
                var member = switchboard.getMember(parseInt($(this).attr("data-id")));
                $("#switchboard-chat-heading").text("Chatting with "  + member.nickname);

            });
           
            $("#switchboard-contacts-list").append(li);
          }

      }
      switchboard.updateMembers(users);
    };

    switchboard.getLastMessageFrom =  function () {
        if (typeof switchboard.messages[switchboard.currentConference.id][switchboard.chattingWith] !== 'undefined') {
          var objs = switchboard.messages[switchboard.currentConference.id][switchboard.chattingWith];
          if (objs) {
              if (objs.length > 0) {
              return objs[ objs.length -1]['message'];         
              }
          }
      }
      return false;
    };
 
    switchboard.updateMessages = function(messages) {
          if (typeof switchboard.messages[switchboard.currentConference.id]  === 'undefined') {
              switchboard.messages[switchboard.currentConference.id] =  {};
            }
        if (typeof switchboard.messages[switchboard.currentConference.id][switchboard.chattingWith] === 'undefined') {
          switchboard.messages[switchboard.currentConference.id][switchboard.chattingWith]  =  {};
          }
        for (var   i  in  messages) {
                    switchboard.messages[switchboard.currentConference.id][switchboard.chattingWith][messages[i].message.id] =messages[i];
          }
      };
    


  switchboard.updateMembers = function(members) {
        if (typeof switchboard.members[switchboard.currentConference.id]  === 'undefined') {
            switchboard.members[switchboard.currentConference.id] = {};
          }

        var  keys = Object.keys(switchboard.members[switchboard.currentConference.id]);
        for (var i in  members) {
            var parsed = parseInt(members[i].id);
            if (!switchboard.oneOf(parsed, keys, true)) {
               switchboard.members[switchboard.currentConference.id][parsed] = members[i];
            }
          }
    };

  switchboard.updateSystemTime = function(time, timestamp) {
         $("#systemTime").text(time);
        switchboard.currentSystemTime = parseInt(timestamp); 
}

  switchboard.getSystemTime = function() {
      return switchboard.currentSystemTime;
    };

  switchboard.say = function(sentance) {
      var sayer = window.speechSynthesis ;

      sayer.speak(new  SpeechUtterance(sentance));
        sayer.resume();
    };


    // when me = true switch to saying your recording in:
  switchboard.updateCounter = function(username, time,time1,deltaUntilMe, deltaColor) { 
    
        if (deltaUntilMe) {
        $("#myRecordingBox").show();
        $("#switchboard-counter1").text(time['hours'] + ":" + time['minutes'] + ":" +time['seconds']);
       
        if (deltaColor) { 
            $("#switchboard-counter1").css({ "color": deltaColor });
            }
        $("#widgetContainerBox").width(600);
        } else {
        $("#widgetContainerBox").width(300);
        $("#myRecordingBox").hide();
        }

         

      if (username) {
        $("#switchboard-recorder-username").text(username);
        $("#switchboard-counter").text(time1['hours'] + ":" +  time1['minutes'] + ":" +time1['seconds']);
      } else {
        $("#switchboard-recorder-username").text("");
        $("#switchboard-counter").text("00:00:00");
      }

  };

  switchboard.setCurrentPsuedoNumber = function(numberToSet) {
      switchboard.currentPsuedoNumber =  numberToSet;
   };
  switchboard.updateUserSettings = function(newConfig, currentConference) {
      var keys = Object.keys(newConfig);
          for (var i in keys) { 
            switchboard.config[keys[i]] = newConfig[keys[i]];
          }
          if (typeof currentConference !== 'undefined') {
      switchboard.currentConference =   currentConference;
            if (parseInt(currentConference.conference_owner_id) === parseInt(switchboard.config['conferenceMemberId'])) {

                  $("#switchboard-conference-manage").show();
              } else if (parseInt(currentConference.conference_owner_id) !== parseInt(switchboard.config['conferenceMemberId']))  {
                  $("#switchboard-conference-manage").hide(); 
              }

          }
          if (typeof switchboard.config['profile_img'] !== 'undefined') {
              $("#switchboard-profile-img").attr("src", "./uploads/" + switchboard.config['profile_img']);             
          }
          if (typeof switchboard.config['nickname'] !== 'undefined'
              && typeof switchboard.config['phoneNumber'] !== 'undefined' 
            ) {

              $("#switchboard-nick-and-number").text(switchboard.config['nickname'] + " (" + switchboard.config['phoneNumber'] + ")");
          }
          var skypeStatus = $("#switchboard-conference-c2call").css("display"); 
          if (skypeStatus !== 'none') {
          $("#switchboard-conference-c2call").click(function() {
              var dialog = {
                  "title": "Click2Call with Skype",
                  "fields": [{
                      "type": "description",
                      "value": "This will execute a skype call, you must have skype installed on your computer",
                      "title": ""
                    }]
                };

               switchboard.dialog(dialog['title'], dialog['fields'],function() {
                      if (switchboard.supportsSkype()) {
                         document.location.replace("skype:" + switchboard.getCurrentConferenceNumber() +"?call");                       
                      } else {
                          switchboard.warn("You don't have skype installed or this browser will not let you click to call. Sorry");
                      }
                },false, {"submit": true, "text": "Click2Call"}, false, false);
              });
                
          }


        // return true by default add logic
      return true;     
  };

  switchboard.saveConferences = function(conferences) {
       switchboard.conferences = conferences;
    };
  switchboard.updateConference = function(conference) {
      switchboard.currentConference = conference;
  };
  // tune off the current live session
  switchboard.tuneOff = function(callback) {
        Twilio.MediaStream.setSilenceLevel(1);
      switchboard.warn("You have left the live session");
      callback();
  };
  switchboard.tuneIn = function(callback) {
       Twilio.MediaStream.setSilenceLevel(0);
       switchboard.warn("You are back in the live session");
        callback();
  };

  switchboard.registerCallback = function(id, functionToRegister) {
      switchboard.callbacks[id] = functionToRegister;
  };
 

  switchboard.performCallback = function(id) {
      if (typeof switchboard.callbacks[id] !== 'undefined') {

      var thisCallback = switchboard.callbacks[id];
      thisCallback(); 
        
      delete switchboard.callbacks[id]; 
      } else if (typeof id === 'string') {
            switchboard[id]();  
      } else { 
          // a functrion
          id(); 
      }
    };
 

          


  switchboard.uid = function() {
        return ("0000" + (Math.random()* Math.pow(36,4) << 0).toString(36)).slice(-4);
  };
   

  switchboard.getMemberById = function(memberId) {
      var members = switchboard.members;
      for (var i in members) {
          if (members[i].id ===memberId) {
              return members[i];
          }
        }
    };

  switchboard.updateRecorder = function(recorder) {
         var member = switchboard.getMemberById(recorder);
        $("#nowRecording").text(member.username + " " + " is now recording");
  };



   switchboard.oneOf = function(subject, matches, intVal) {
        for (var i in matches) {
          if (intVal) {
            if (parseInt(matches[i]) === parseInt(subject)) {
              return true;
            }
          } else {
            if (matches[i]  ===subject) {
                return true;
            }
          }
        }
        return false;
    }

  switchboard.defaultSetup = function() {
      window.onunload = function() {       
             Oneline.once({
                    "obj": "generic",
                    "data": {
                      "type": "updateStatus",
                      "data": {
                          "conferenceId": switchboard.config.conferenceId,
                          "conferenceMemberId": switchboard.config.conferenceMemberId,
                          "guest": switchboard.config.guest,
                          "status": "OFF"
                        }
                      }
              });
        }; 
        
    };
 
  switchboard.updateUser = function(conferenceMemberId, status) { 
         switchboard.members[conferenceMemberId]['status'] =status; 
        $("#" + conferenceMemberId +"_member").find("i").attr("class",switchboard.defaults['status' + switchboard.titleCase(status)]);
    };

  switchboard.logout = function() {
      switchboard.waitForBoxer(function()  {
        switchboard.dialog("Are you sure?", [{       
                    "type": "description",
                    "title": "",
                    "parentId": "",
                    "value": "This will end your recording session, and display your status as away"
          }], function() {
               
      
              Oneline.once({
                    "obj": "generic",
                    "data": {
                    "type":"logout",
                    "data": {
                        "conferenceId":switchboard.config.conferenceId,
                        "conferenceMemberId": switchboard.config.conferenceMemberId,
                      }}}); 
        }, false, {"submit": true, "text": "Yes, log me out"}, false);
      });
       Oneline.acceptAfter(Date.now());
    };
      
 
  // get the media url for the current
  // recorder this should 
  // return the twilio webrtc audio stream url
  // http://{server}/{stream}.mp3


  switchboard.getMediaStream = function(){
      return switchboard.base_url +"/?r=interface/stream&conferenceId=" + switchboard.config.conferenceId;

  };

  switchboard.prettyText = function(amount,text) {
      if (text.length  > amount) {
          return text.substring(0, amount) + "..";
      }
      return text;
  };

  switchboard.initUI = function() {
      
      switchboard.defaultSetup(); 
      //switchboard.initDevice(switchboard.currentDeviceToken); // init twilio
      var splashContainer  =  document.createElement("form");
      $(splashContainer).attr("method","POST");
      var container = document.createElement("div");
      var randomBackground = switchboard.splashBackgrounds[Math.floor(Math.random(0, switchboard.splashBackgrounds.length))];
      $(container).attr("class","container");
      
      var firstContainer = document.createElement("div");
      $(splashContainer).attr("class","switchboard-splash");
      $(splashContainer).attr("style", "background: url(" + randomBackground + ") repeat-x");
      $(firstContainer).attr("class","switchboard-first-container");
      var clear = document.createElement("div");
      var field1 = document.createElement("div");
      var field0 = document.createElement("div");
      var field2 =  document.createElement("div");
      var guestField = document.createElement("input");
      var labelForGuest = document.createElement("label");
      var hr = document.createElement("hr");
      $(guestField).attr("is-checked","no");
      /*(
      $(guestField).click(function() {
          if ($(this).attr("is-checked") === "yes") {
          $(this).attr("is-checked", "no");
          } else {
          $(this).attr("is-checked", "yes");
        }
        });
 
        */

       $(labelForGuest).html("Are you a guest?"); 
      $(guestField).attr( "type", "checkbox");
      $(guestField).attr("id", "guestField");
      $(clear).attr("class", "clear");
      $(field0).append(labelForGuest);
      $(field0).append(guestField);
      $(field0).append(hr);
      $(field1).attr("class", "field-splash");
      $(field2).attr("class", "field-splash");
      var h2 = document.createElement("h2"); 
      $(h2).attr("class", "heading");
      $(h2).text("Welcome to the switchboard, please enter your nickname, and we will join you in the conference");
      var label = document.createElement("label");
      $(label).text("Your nickname"); 
      $(field1).attr("class", "field-splash");
     
      var  input = document.createElement("input");
      $(input).attr("placeholder", "Your nickname");
      $(input).attr("id", "nickname");      

      $(firstContainer).append($(clear).clone());
      $(field1).append($(clear).clone());
      $(field1).append(label);
      $(field1).append($(clear).clone());
      $(field1).append(input);

      var label2 = document.createElement("label");
     $(label2).text("Your Phone Number (needed)");
      var input2 = document.createElement("input");
      $(input2).attr("id", "phoneNumber");
      $(input2).attr("placeholder", "+15146959075");

      $(firstContainer).append(h2);
      $(firstContainer).append($(clear).clone());

      $(field2).append($(clear).clone());
      $(field2).append(label2);
      $(field2).append($(clear).clone());
      $(field2).append(input2);
        // second containers
        $(firstContainer).append(field0);
          $(firstContainer).append(field1);
      $(firstContainer).append(field2);
        $(firstContainer).append($(clear).clone());
      var secondContainer = document.createElement("div");
      $(secondContainer).attr("class", "second-container");
      var field3 = document.createElement("div");
      var hOr = document.createElement("h2"); $(hOr).attr("class", "hOr");
      $(hOr).text("OR");
      var hr = document.createElement("hr");
      var label3 = document.createElement("label");
      $(label3).html("Login using your one time access code<br />");
      var input3 = document.createElement("input");
      $(input3).attr("id", "one_time_access_code");
      $(input3).attr("placeholder", "e.g: 1bf1");
        var clear3 = document.createElement("div");
      

          $(clear3).attr("class", "clear");
        $(clear3).attr("class", "clear");

        $(field3).attr("class", "field-splash");
      $(field3).append(label3);
        $(field3).append($(clear).clone());
 $(field3).append(input3);
      var disclaimer = document.createElement("div");
      $(disclaimer).attr("class","disclaimer");
      $(disclaimer).text("This was texted to you when you first registered");
      $(secondContainer).append(hr);
      $(secondContainer).append(hOr);
      $(secondContainer).append(clear3);
      $(secondContainer).append($(clear3).clone());
      $(secondContainer).append(field3);
      $(secondContainer).append($(clear3).clone());
      $(secondContainer).append(disclaimer);

      $(secondContainer).append($(hr).clone());
      var button = document.createElement("button");
      $(button).text("Join >>");
      $(button).attr("class","dc_g_button blue");
      
      var clear = document.createElement("div");
      $(clear).attr("class", "clear");
      $(secondContainer).append(button);
        

      $(container).append(firstContainer);
      $(container).append($(clear).clone());
      $(container).append(secondContainer);
      $(splashContainer).append(container);

      $(switchboard.main_container).append(splashContainer);
      $(splashContainer).submit(function(ev) {
          ev.stopPropagation();
          ev.preventDefault();
          switchboard.loginFunc();
      });
            
    };
    switchboard.loginFunc= function() {
        var oneTimeAccessCode = $("#one_time_access_code").val();
          var guest = false;
          if (oneTimeAccessCode !== "") {
              switchboard.initChat(guest);
          } else { 
          var guest = $("#guestField").prop("checked");
          if ( !guest) {
          var phoneNumber = $("#phoneNumber").val();
          if (!switchboard.validateNumber(phoneNumber)) {
              return alert("The phone number you entered does not match the requirements please make sure it looks as follows: +16959075"); 
          }

          // guest chgeck
          //var guest =   $("#guestField").prop("checked");


            var nickName = $("#nickname").val();
            var validated = switchboard.validateNickname(nickName);
            if (validated['error']) {

          //j 
                return alert("the nickname you entered had errors " + validated['error_string']);
              }
            }
          } 
          switchboard.initChat(guest); 
        };
      

   switchboard.buildUI = function() {
      var modalShiftFix =  $("<div class='modal-shiftfix'></div>");
      var navBar = $("<div class='navbar navbar-fixed-top'></div>");
      var container = $("<div class='container-fluid top-bar'></div>");
      var pullRightOuter = $("<div class='pull-right'></div>");
      var pullRight = $("<ul class='navbar navbar-nav pull-right'></ul>");

      var userNav = $("<li class='dropdown user-hidden xs'></li>");
      var userIcon = $("<img id='switchboard-profile-img'  class='avatar' style='width: 64px; height: 64px; '/>");
      var userName = $("<div id='switchboard-nick-and-number' class='username'></div>");
      var innerUser = $("<ul class='dropdown'></ul>");

      var footer = $("<div class='footer'></div>");
      var footerMenu = $("<ul class='footerMenu'></ul>");
      var systemTime = $("<li><h5 id='systemTime'></h5></li>");
      $(footer).append(footerMenu);
      $(footerMenu).append(systemTime);
       

      var warning = $("<div class='switchboard-warning' id='switchboardWarning'></div>");
        $(switchboard.main_box).append(warning);


      $(switchboard.main_box).append(modalShiftFix);

      $(navBar).append(container);

      $(container).append(pullRightOuter);
      $(userNav).append(userIcon);
      $(userNav).append(userName);

    
      $(pullRight).append(userNav);
      $(pullRightOuter).append(pullRight);
      var menuOptions = [{
            "icon": "account",
            "text": "Logout",
            "action": "logout"
      },
      {
          "icon": "account",
          "text": "My Account",
          "action": "myaccount"
      }];
      for (var i in menuOptions) {
            var li = $("<li class='dropdown'></li>");
            var a = $("<a href='#'></a>");
            $(a).append($("<i class='" + menuOptions[i].icon + "' />"));
            $(a).text(menuOptions[i].text);
  
            $(a).attr("data-action", menuOptions[i].action);
            $(a).click(function() {
                 return switchboard[$(this).attr("data-action")]();
            });
            $(li).append(a);
              $(innerUser).append(li);
      
      }
      var anchorOfLogo = $("<a class='logo'>" + switchboard.applicationName + "</a>");

      $(container).append(anchorOfLogo);
      
      var mainNav = $("<div class='container-fluid main-nav clearfix'></div>");
      var navCollapse = $("<div class='nav-collapse'></div>");
      var navBarMenu = $("<ul class='nav'></ul>");
      var navItems = [{ 
              "text": "Chat",
              "action": "viewChat",
              "id": "chat"
      },
      {
            "text": "Schedule Recording",
            "action": "startRecording",
            "id": "startRecording"
      },
      {
          "text": "Stop Recording", 
          "action": "stopRecording",
          "id": "stopRecording"
      },
      {
          "text": "Recoridngs",
          "action":"viewRecordingsPre",
          "id": "viewRecordings"
      },
      {
          "text": "View Conferences",
          "action": "viewConferencesPre",
          "id": "viewConferences"
      },
      {
          "text": "My Account",
          "action": "myAccount",
          "id": "myAccount" 
      },
      {
          "text": "Logout",
          "action": "logout",
          "id": "logout"
      }
      ];
        
      $(navCollapse).append(navBarMenu); 
      $(mainNav).append(navCollapse);
    
      $(navBar).append(mainNav); 
 

      for (var i in navItems) {
          var li = $("<li></li>");
          var a =  $("<a href='#'></a>");
          $(a).text(navItems[i].text);
          $(a).attr("data-action",navItems[i].action);
          $(a).click(function() {
              switchboard[$(this).attr('data-action')]();
          });
          $(li).append(a);
          $(navBarMenu).append(li);
      }
     $(navBarMenu).append($("<div class='clear'></div>"));
 
      $(modalShiftFix).append(navBar); 
      var clear = $("<div class='clear'></div>");
      $(modalShiftFix).append(clear);
    
      var mainContent = $("<div class='container-fluid main-content clearfix' id='switchboard-container'></div>"); 
      var mainWrapper = $("<div class='main-wrapper'></div>");
      var clock = switchboard.widgetCounter();
      var chat = switchboard.widgetChat();
      var utils = switchboard.widgetUtils();
      
     $(modalShiftFix).append($("<div class='clear'></div>"));
      $(mainWrapper).append(clock);
      $(mainWrapper).append($("<div class='clear'></div>"));
      $(mainWrapper).append(utils);
      $(mainWrapper).append(chat);
     
      $(mainWrapper).append(footer); 

      $(mainContent).append(mainWrapper);
      $(modalShiftFix).append(mainContent);

    };

  switchboard.widgetCounter = function() {
        
        var outer = $("<div style='background: #010101; color: #FFF; width:100%;margin-top:115px; position:relative;float:left;padding-top:25px; height: 250px; '></div>");
        var widgetContainer = $("<div class='widget-clock'></div>");
        var widgetContainerInner = $("<div id='widgetContainerBox' style='margin:0 auto; width: 600px;'></div>");
        var whenIAmRecording = $("<div style='float:left; width: 300px; text-align:center;' id='myRecordingBox'></div>");
      var currentlyRecording = $("<div style='float:left; width: 300px; text-align:center;'></div>"); 
       var usernameOfRecorder = $("<small><div id='currentSwitch'>Currently Recording:</div> <p id='switchboard-recorder-username'></p></small>");
        var conferenceManage = $("<button style='float: left; margin-right 5px; ' id='switchboard-conference-manage' class='dc_g_button green'>Manage Conference</button>");
        var conferenceClickToCall = $("<button style='float: left; ' id='switchboard-conference-c2call' class='dc_g_button blue'>Click To Call[skype]</button>");


       var internal = $("<h2 id='switchboard-counter'></h2>");
        var phoneNumberToDial = $("<h5>By phone dial: <small id='switchboard-conference-number'>" +  switchboard.getCurrentConferenceNumber() + "</small></h5>");
        var urlStream = $("<h5>By Stream go to: <a id='switchboard-conference-stream' href='" + switchboard.getMediaStream() +"' target='_blank'>Click here</a></h5>");

        var myUsername = $("<small><div id='currentMySwitch'>You Will Record In:</div></small>");
        var internal1 = $("<h2 id='switchboard-counter1'></h2>");
      
       
        $(whenIAmRecording).append(myUsername);
          $(whenIAmRecording).append(internal1); 

        $(conferenceManage).hide();
        $(conferenceManage).click(function() {       
            switchboard.manageConferencePre();
        });
      
       $(internal).text(switchboard.counter);
         

        $(currentlyRecording).append(usernameOfRecorder); 
        $(currentlyRecording).append(internal);
    
        $(widgetContainerInner).append(whenIAmRecording);
        $(widgetContainerInner).append(currentlyRecording);
        $(widgetContainerInner).append(phoneNumberToDial);
        $(widgetContainerInner).append(urlStream);
        $(widgetContainerInner).append(conferenceManage);
        $(widgetContainerInner).append(conferenceClickToCall);

        $(widgetContainer).append( widgetContainerInner);
        $(widgetContainer).append($("<div class='clear'></div>"));
        $(whenIAmRecording).hide();
        $(outer).append(widgetContainer);
      return outer; 
  };

  switchboard.widgetUtils = function() {
      var outerDiv = $("<div class= '' style='float:left; width: 10%; '>");
      var mainUtils = $("<ul class='main-utils'>");
      var utils = [{
          "type": "recording",
          "text": "Start Recording",
          "action": "startRecording",
          "icon": ""
       },
        {
            "type": "stop_recording",
            "text": "Stop Recording",
            "action": "stopRecording",
            "icon": ""
        }
      ];

      var outer = $("<ul class='recording-utils'></ul>");
      for (var i in utils) {
          var li = $("<li class='recording-util'></li>");
          var ico = $("<i class='" +utils[i].icon + "' />");
          $(li).attr("data-action", utils[i].action);
          $(li).text(utils[i].text);
          $(li).append(ico);
          $(outer).append(li);
          $(li).click(function() {
               switchboard[$(this).attr("data-action")]();
          });
      }
      $(mainUtils).append(outer);  
      $(outerDiv).append(mainUtils);
    return outerDiv;
    };
        


  switchboard.widgetChat = function()  {
        var chatOuter = $("<div  class='row'></div>");
        var chatBox = $("<div class='col-lg-12'></div>");
        var scrollable = $("<div class='widget-container chat chat-page scrollable'></div>");
        var heading = $("<div class='heading'></div>");
        var headingInner =  $("<div id='switchboard-chat-heading' class='heading'></div>");
        var contactsList = $("<div class='contact-list' style='z-index: 1; '></div>");
        var contactsListHeading = $("<div class='heading'></div>");
        var contactsListInner = $("<ul style='background: #FFF;' id='switchboard-contacts-list'></ul>");
        $(contactsListHeading).text("Chat Participants");
       
       var globalIcon  = $("<i class='fa fa-icon globe' style='float: left; margin-left: 2px;width:16px;height:16px; cursor:pointer; ' ></i>");
      
        $(globalIcon).click(function() {
              $("#switchboard-chat-heading").text(switchboard.applicationName + " Global Chat");
              switchboard.updateSince = false; //not applicable to global we need to fetch from all
              switchboard.chattingWith= "global";
              switchboard.prependMessages = false;
          });

         $(contactsList).append(contactsListHeading);
        $(contactsList).append(contactsListInner);
        $(headingInner).text(switchboard.applicationName + " Global Chat");
        $(heading).append(headingInner);
        $(heading).append(globalIcon);
        var widgetContent = $("<div class='widget-content padded'></div>");
        var widgetChatMessages = $("<ul id='switchboard-chat-messages'></ul>");
        var postMessage = $("<div class='post-message'></div>");
        var inputForm = $("<input class='form-control' id='message_input'/>");
        var submit = $("<input type='submit' value='Send' />");
        $(inputForm).keyup(function(evt) {
            if (evt.keyCode === 13) {
              switchboard.sendMessage($(this).val());
            }
        });
        $(submit).click(function() {
              switchboard.sendMessage($("#message_input").val());
        });
        // initially none
        $(chatBox).append(scrollable);
        //$(scrollable).append(widgetContent);
        $(scrollable).append(contactsList);
        $(scrollable).append(heading);
        $(scrollable).append(widgetContent);
        //$(widgetContent).append(contactsList);
        $(widgetContent).append(widgetChatMessages);
        $(widgetContent).append(postMessage);
        $(postMessage).append(inputForm);
        $(postMessage).append(submit);
        $(chatOuter).append(chatBox);
        $(chatOuter).append($("<div class='clear'></div>"));
      return chatBox;
    };

      
 
                 
 


       

        
   switchboard.initChat = function(guest) { //when guest set do not use the other info
      if (guest) {
        switchboard.config.guest = true;
        switchboard.config.nickname = ""; // until given 
        switchboard.config.phoneNumber = "";
        switchboard.config.oneTimeAccessCode = "";
        var newAccessCode = false;
        $(".switchboard-splash").hide();
      } else {
        switchboard.config.nickname = $("#nickname").val();
        switchboard.config.phoneNumber = $("#phoneNumber").val().replace(/\s|\(/,"");
        switchboard.config.oneTimeAccessCode = $("#one_time_access_code").val() === "" ? false: $("#one_time_access_code").val();
          var newAccessCode = switchboard.config.oneTimeAccessCode?  false : switchboard.uid(); 
          $(".switchboard-splash").hide();
      }

       var outerContainer = document.createElement("div");
       var leftHandNavigation = document.createElement("div");
        Oneline.setup({ module: "switchboard_chat",  host: document.location.host, freq:  1000, port: 9000 });
        
        Oneline.ready(function() { 
          console.log("oneline is ready");
          Oneline.once({
              "obj": "generic",
              "data": {
                "type": "activeConference",
                "data": {
                  }
                }
            });
            
            Oneline.pipeline(function(response) {
                if ($("#switchboard-container").get().length === 0) {
                 switchboard.buildUI();
                }
           
  
                console.log("response type is:"); 
                console.log(response.response.type); 
                if (response.status === 'ok') {
                    if (response.response.type === "activeConference" && Oneline.isMe(response)) { 
                          if (!response.response.error) {
                              console.log("activeconference response was:");
                              console.log(response.response);
                             switchboard.config.conferenceId =  response.response.conferenceId;
                             Oneline.once({
                                  "obj": "generic",
                                  "data": {
                                  "type": "joinRoom",
                                  "data": {
                                      "nickname": switchboard.config.nickname,

                                      "phoneNumber":switchboard.config.phoneNumber,
                                      "oneTimeAccessCode": switchboard.config.oneTimeAccessCode,
                                      "conferenceId": response.response.conferenceId,
                                      "newAccessCode": newAccessCode,
                                      "hoursAhead": parseInt(response.response.hoursAhead),
                                      "hoursBehind": parseInt(response.response.hoursBehind),
                                      "guest": switchboard.config.guest,
                                      "offset": switchboard.getHourOffset()
                                    }
                                  }
                                });
                              //switchboard.reSync(switchboard.currentDeviceToken);
                          } else {
                               switchboard.warn("No active conference, please come back later..");
                          }
   
                  } else {                        
                    if  (response.response.type ==='joinRoom' && Oneline.isMe(response)) {

                        //switchboard.initDevice(switchboard.currentDeviceToken); 
                        if (!response.response.error) {
      
                              if (!switchboard.config.guest) {
                            switchboard.setCurrentPsuedoNumber(response.response.psuedoNumber);
                              }
                            var updateStatus = switchboard.updateUserSettings( {
                                "conferenceMemberId": response.response.conferenceMemberId,
                                "conferenceId": response.response.conferenceId,
                                "nickname": response.response.user.nickname,
                                "profile_img": response.response.user.profile_img,
                                "phoneNumber": response.response.user.phone_number,
                                "hoursBehind": parseInt(response.response.hoursBehind),
                                "hoursAhead": parseInt(response.response.hoursAhead)
                              },
                              response.response.conference 
                            );

                            
                            $(".username").text(switchboard.config.nickname);
                            $("#switchboard-profile-img").attr("src",switchboard.config['profile_img']);
                            
                            if (updateStatus) {
                              //switchboard.runCore();
                              switchboard.reSync();
                              //if (!switchboard.config.guest && !response.response.guest) {
                               // switchboard.initDevice(switchboard.currentDeviceToken); 
                              // }
                              //switchboard.reSync(switchboard.currentDeviceToken);
                              switchboard.runCore();
                             }
                        } else {
                            $(switchboard.main_container).hide();        
                            switchboard.warn(response.response.message);
                        }
                      } else {
                        if (switchboard.config.conferenceMemberId && switchboard.config.conferenceId) {
                          if (response.response.type === 'updateAccount' && Oneline.isMe(response)) {
                            if (!response.response.error) { 
                                switchboard.warn(response.response.message, "success");   
                                switchboard.updateUserSettings(response.response.user); 
                               // switchboard.updateUserInfo(response.response.user);
                            } else { switchboard.warn(response.response.message); 
                            

                            }
                            $.boxer("close");
                            switchboard.runCore();

                        } else if (response.response.type === 'getMessages' && Oneline.isMe(response)) {
                              setTimeout(function() { 
                                switchboard.showMessages(response.response.messages);
                              }, 0);
                              switchboard.runCore(); 
                        } else if (response.response.type === "viewUpcomingRecordings" && Oneline.isMe(response)) { 
                            if (!response.response.error) {
                                  switchboard.waitForBoxer(function() { 
                                    switchboard.viewUpcomingRecordingsPost(response.response.recordings);
                                  });
      
                              } else {  
                                  switchboard.waitForBoxer(function() {
                                    switchboard.warn(response.response.message); 
                                  });
                              }
                            switchboard.runCore(); 
                        } else if (response.response.type === 'viewPreviousRecordings' && Oneline.isMe(response)) { 
                              
                            if(!response.response.error) {
                                switchboard.waitForBoxer(function() {
                                    switchboard.viewPreviousRecordingsPost(response.response.recordings);
                                  });
                            } else {
                                 switchboard.waitForBoxer(function() {
                                  switchboard.warn(response.response.message);
                                 });
                            }
                            switchboard.runCore();
                        } else if (response.response.type === 'viewConferences' && Oneline.isMe(response)) {
                            if (!response.response.error) {

                                console.log("got conferences");
                                console.log(response.response);
                        
                                switchboard.waitForBoxer(function() {
                                    switchboard.viewConferencesPost(response.response.conferences);
                                  });
                                switchboard.runCore();
                            } else {
                                  switchboard.warn(response.response.message);
                            }
                            switchboard.runCore();
                        } else if (response.response.type === "getRecordingAndPlay" && Oneline.isMe(response)) {
                                                       
                              if (!response.response.error) { 
                                  switchboard.playRecordingPlayerPre(response.response.recording);
                              } else {
                                  switchboard.warn("Could not play this recording at this moment");
                              }
                              switchboard.runCore(); 
                        } else if (response.response.type === "getAllConferenceMembers" && Oneline.isMe(response)) {
                              var members = response.response.conferenceMembers;
                            
                              if (!response.response.error) {
                              switchboard.getConferenceMembersAndFillPost(members);
                              }
                              switchboard.runCore();
                        } else if (response.response.type === 'createConference' && Oneline.isMe(response)) {
                            if (response.response.created) {
                              switchboard.warn("You have created this conference successfully");

                              switchboard.pendingConferenceId =response.response.conferenceId;
                              switchboard.waitForBoxer(function() {
                                switchboard.goToConferenceDialog();
                              });
                            } else {
                              switchboard.warn("Could not create conference");
                            }
                            switchboard.runCore();
                        } else if (response.response.type === 'manageConference' && Oneline.isMe(response)) {
                            if (!response.response.error) {
                              switchboard.waitForBoxer(function(){
                              switchboard.warn("You have updated this conference");
                              });
                              
                            } else {
                              switchboard.warn(response.response.message);
                            }

                            switchboard.runCore();
    
                        } else if (response.response.type === 'switchConference' && Oneline.isMe(response)) {
                          if (response.response) {
                              if (response.response.switched) {
                                   
                                  switchboard.chattingWith ="global"; 
                                  switchboard.waitForBoxer(function() { 
                                    switchboard.updateUserSettings({ 
                                       "conferenceMemberId": switchboard.config.conferenceMemberId, 
                                        "conferenceId": response.response.conference.id
                                    },  response.response.conference);

                                    switchboard.currentConferenceNumber =response.response.conferenceNumber; 
                                    switchboard.currentRecordingNumber = response.response.recordingNumber;
                                    switchboard.currentPsuedoNumber = response.response.psuedoNumber;
                                    switchboard.currentDeviceToken = response.response.conferenceToken;
                                    switchboard.reSync();
                                    switchboard.warn("You are now in " + response.response.conference.conference_title);
                                  });
                              }
                          }

      
                           switchboard.runCore();
    
                        } else if (response.response.type === "viewConferenceAuth") {
                              if (!response.response.error) {                          
                                 switchboard.manageConferencePost(response.response.conference, false);
                              } else {
                                switchboard.warn(response.response.message);
                              }
        

                        } else if (response.response.type === 'logout') {
                            switchboard.waitForBoxer(function() { 
                              switchboard.warn("Thank you, you are now being logged out");
                              setTimeout(function() {
                              document.location.replace("./?r=interface/index");
                              }, 500);
                            });
                        } else if (response.response.type ==='core' && Oneline.isMe(response)) {
                             
                              if (!switchboard.inSetup) { 
                                switchboard.inSetup =true;
                              var messages = response.response.messages;                     
                              var members = response.response.members;
                              if (switchboard.prependMessages) {
                                    for (var i in switchboard.messages[switchboard.currentConference.id][switchboard.chattingWith]) {
                                      messages[i]  = switchboard.messages[switchboard.currentConference.id][switchboard.chattingWith][i];
                                    }
                                    messages = switchboard.sortMessages(messages);
                            }
               
                             
                                if (response.response.chattingWith ===  switchboard.chattingWith) {
                                  setTimeout(function() {
                              switchboard.showMessages(messages);
                                      }, 0);
                                  }
                                setTimeout(function() {
                                switchboard.showMembers(members);
                                }, 0);

    

                              var deltaUntilRecord = false, deltaUntilThisMemberDone = false, deltaAndColor=false, usernameOfRecorder = false, myRecordingId = false, humanDate1=false, humanDate2=false, deltaAndColor = false;
       
                              if (typeof response.response.deltaUntilRecord !== 'undefined') { 
                                    deltaUntilRecord = response.response.deltaUntilRecord;
                                    myRecordingId = response.response.myRecordingId;
                              }
                              if (typeof response.response.deltaUntilThisMemberDone !== 'undefined') {
                                  deltaUntilThisMemberDone = response.response.deltaUntilThisMemberDone;
                                }
                              if (typeof response.response.usernameOfRecorder !== 'undefined') {
                                 usernameOfRecorder = response.response.usernameOfRecorder;
                              }
                              if (typeof response.response.endedRecording !== 'undefined') {
                                  endedRecording = response.response.endedRecording;
                              }

                              if (deltaUntilRecord){ 
                                  var humanDate1= switchboard.humanizeDelta(parseInt(deltaUntilRecord));
                                  var deltaAndColor = switchboard.readDelta(parseInt(deltaUntilRecord));
                                  var  matchesDelta=  switchboard.matchesDelta(myRecordingId, parseInt(deltaUntilRecord));

                                    /*
                                  if (matchesDelta) {
                                        switchboard.say("You will be recording in " + humanDate1['hours'] +  "hours , " + humanDate1['minutes'] + " minutes and " + humanDate1['seconds'] + " seconds");
                                    }
                                    */
                                } 

                                if (deltaUntilThisMemberDone) {
                                      var humanDate2 =  switchboard.humanizeDelta(parseInt(deltaUntilThisMemberDone));

                                        
                                     // if (humanDate['hours']  >0) {
                                      //      switchboard.

                                }                               

                                switchboard.updateCounter(usernameOfRecorder, humanDate1,humanDate2,deltaUntilRecord, deltaAndColor); 
                                switchboard.updateSystemTime(response.response.currentSystemTime, response.response.currentSystemTimestamp);
                              switchboard.runCore(); 
                                switchboard.inSetup= false;
                                }

                        } else if (response.response.type === 'saveRecording' && Oneline.isMe(response)) {
                              
                            if (!response.response.error) {
                            switchboard.warn("We have saved your recording");
                            } else {
                            switchboard.warn("Could not save your recording");
                            }
                            switchboard.runCore();
                            
                        } else if (response.response.type === 'sendMessage' && Oneline.isMe(response)) {
                              if (response.response.saved)  {
                                switchboard.warn("You have sent this message successfully", "success");
                              } else {
                                switchboard.warn("Could not save message");
                              }
                              switchboard.runCore();

                        } else if (response.response.type === "updateStatus" && Oneline.isMe(response)) {
                              if (response.response.conferenceMemberId) {
       
                       
                                  switchboard.updateUser(response.response.conferenceMemberId, response.response.status);
                              }
                              switchboard.runCore();
                        } else if (response.response.type === 'startRecording' && Oneline.isMe(response)) { 
                              if (response.response.started) {
                                  switchboard.warn(response.response.message, "success");
                                  $.boxer("close");
                              } else {
                                switchboard.warn(response.response.message);
                               }
                            switchboard.runCore();
                        } else if (response.response.type ==='stopRecording' && Oneline.isMe(response)) {
                            if (response.response.stopped) {
                                switchboard.warn(response.response.message, "success");
                                $.boxer("close");
                            } else {
                                switchboard.warn(response.response.message);
                                $.boxer("close");
                            }
                            switchboard.runCore();
                          } else if (response.response.type === 'incomingCall') {

                              if (response.response.accepted) {
                                  switchboard.warn(response.response.message); 
                                  switchboard.incomingConnection.accept();
                              } else {
                                // void a user called at the wrong time
                              }
                              switchboard.runCore();
                          }
                       
                                                   
                    } else {
                        if (!switchboard.no_entry_warned) {
                         switchboard.warn(response.response.message);
                        switchboard.no_entry_warned = true;
                        }
                    }
                   }
                 }
              } else if (response.status === 'error' || response.status === 'empty') {
                   
                     switchboard.warn("Something went wrong. Please try again");              

                }
   
          }).run(); 
      });
    };
                  
}).call(this);
      
  

 
       

   

      




   

