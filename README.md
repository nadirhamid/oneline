Oneline  (A Python Project)
=========================================================
![alt tag](http://infinitet3ch.com/assets/oneline-logo.png)

Oneline adds real time streaming to your web app's data



What you will find
=========================================================

In oneline you will find a series of server and client modules that work together
to stream data in your web apps. This data can then be refined and served in a variety
of ways.

Getting Started (command line)
=================================================

Before anything you should:

	make
	
this will install oneline and its dependancies. It will also start the oneline server if everything goes well.

To make a simple module, do:

	oneline --init "my_module"

This will create the needed files for writing your first oneline module.

Some Examples
========================================================

Below I've included some examples using CoffeeScript and
Python.

Geo Examples
-------------------------------------------------------

1. Update all views with data every 5000 lat coords moved

	Here's an example of my
	Client side code:
	
		Oneline.setup({		
		   'host': document.location.host,
		   'port': 9000, // the standard port oneline runs on
	     	   'module': 'GeoMod'
		});
         	Oneline.geolocation({
            	  range: 0.0000050
         	});
		Oneline.ready(function() {
	   		Oneline.pipeline(function(response) {
	      			if (response.data && response.good) {
	         			console.log(response.data); //the data
	      			} else { // something went wrong
	         			console.log(response);
	      			}
	   		}).run();
	 	});
	 
	And the server:
	
		from oneline import ol
		
		class GeoMod(ol.module):
		    def start(self):
		        self.pipeline = ol.stream()
		
		    def receiver(self, message):
		    	self.pipeline.run(message)
		        
		    def provider(self, message):
		    	self.pipeline.run(message)
		    
		    def end(self):
		    	""" cleanup """

Event examples
-------------------------------------------------------


1. Filter data every 2000 coords moved, afterwards further refine with a city

		Oneline.geolocation({
			'every': 2000
		});
		Oneline.event({
			'city': Oneline.value('like', 'Montreal')
		});
		Oneline.ready(function() {
			Oneline.pipeline(function(response) {
				if (response.good && response.data) {
				// got something
					myApp.fillData(response.data);
				}
			}).run();
		});
  


			

	
To include the client side library
-------------------------------------------------------------------------------------
	from the CDN:
	<script type="text/javascript" src="http://getoneline.com/lib/oneline-1.0.0.min.js">


	or locally
	<script type="text/javascript" src="/oneline.min.js">

That's it for installing.

Writing modules
=====================================================

Now that you've installed, you should be ready
to write some modules. Before you do, a few words:

1. All modules are stored in {oneline_root}/modules. These are regular Python
files that are passed to cherrypy. You will find some examples in ./examples. 

2. Configs can be found in ./conf.. These configs carry things like database information, standard settings,  etc. They should follow the same naming convention as their
modules. Like so:
	
	MyAwesomeModule.py -> MyAwesomeModule.conf
	
	Here is what a config might look like:
	
		db_type = 'mysql'
		db_user = 'root'
		db_host = 'localhost'
		db_table = 'a_table'
		db_pass = 'ask_an_admin'
		db_database = 'my_database'
		db_commit_timeout = 3600
		
		
3. Every module uses four methods that are unique to oneline -- these are
<i>start</i>, <i>receiver</i> and <i>provider</i> and <i>end</i>. Like there name suggests they
open, receive and provide messages to the websocket connection.

4. All modules need one major table to extract data from, this will be the
used for all the computations. This table should (not needed) have a field that is a primary 
key.

5. Order is very important to oneline. In fact it retains all data from the first object
used, afterwards refines according to its other objects. So while design is up to the
programmer, I would definitely put it out there that this project's style is not commutative.
More, oneline merits a 'confidence' rank for every result in a finding of data. This is how it works:

Suppose we have 3 modules, namely: Geolocation, Time and Event

If Geolocation matches a set of data the confidence level becomes one
Next when the Time object matches a subset the confidence level for this set becomes two
Finally when event matches a set of data its objects take three

The result will be sorted by the highest confidence rank



Now.. 
============================================================================================

You are now ready to write it's client code.  Client code
is exactly like the server code minus the dom.  You will find I have included
some examples in ./examples,  these should give you an idea as to how one works.

When writing for the client it is important to use things like Oneline.ready/0 and
Oneline.setup/1. These ensure our connections are setup correctly and under the hood
also check for fallbacks like XHR. 





----------------------------------------------------------------------------------------

		
Third Party Libraries
=======================================================

Oneline uses web2py's DAL and supports the following databases:

  - SQLite & SpatiaLite
  - MySQL
  - Postgres

Other libraries include

  - ws4py
  - cherrypy

Contributing & More
========================================================

Oneline is very young and ambitious, a lot of changes will be made it.  
Due to brevity and being only maintained by one person (me), it has been difficult to fully document the code and include the amount of examples I wanted to, I will continue to work on this project, also
try to document it to the best of my ability.

Nadir Hamid<i>[matrix.nad@gmail.com]</i>
