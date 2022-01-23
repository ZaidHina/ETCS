# ETCS
ETCS ---> Emergency Traffic Control System 

This Project Requires:

Python 3.x , Android/IOS application , Database , Mqtt Broker Server (You can use Eclipse Mosquitto as an open source one) ,  Board with leds and their connections.


About The Project:

ETCS focus on open traffics (move cars faster on the roads) for the ambulance cars on it way to patient/hospital.


About Its Working:


Each Ambulance Driver will have a record at the server and his phone number (on the database) to verify using the app, which will send to server the location of the driver
each 100 m or 4.5 seconds acheived by S=D/T (S: Speed , D: Distance and T: Time) with average speed about 80 km/h.

At this time server will handle the informations (locations) by searching for near traffics blocks (withen 1Km) and once it found one, it will give 3 attempts to find all the possible
traffic blocks to turn all possible traffic lights to green.

At this time, the server will stay receiving the location of the ambulance to determine if it passed one of traffic lights or not , if yes turn all traffic lights to normal situation.

