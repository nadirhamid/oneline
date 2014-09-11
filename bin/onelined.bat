if %1% == "/start"
	echo "Starting oneline server (c) 2014 Nadir Hamid"
	nohup python ../server.py &
	echo "It worked. now accepting connections on 127.0.0.1:9000"

if %1% == "/start"
	echo "Stopping oneline server"
	echo "All connections to oneline have closed. Come again :("
fi