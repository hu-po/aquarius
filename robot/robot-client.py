"""
this script (running inside a docker container in agx orin) sends commands to the robot server (running on pi bare metal) 

the commands are sent over a socket connection to the robot server, possible commands are:

q: quit
r: start record
c: stop record
p: play once
P: loop play / stop loop play
s: save to local
l: load from local
f: release mycobot

because of this the total information sent is minimal, just these commands

each command will be "clicked" on by the user in the frontend-pc application, in the robot page

each command will have an emoji button on the frontend-pc application, in the robot page
"""