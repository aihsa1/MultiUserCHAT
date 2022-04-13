# Multi User Chat - CLI Version
## Made by Ran David
----------------------------------
# Description
This repo is a client-server system that enables communicate with others in a chat room.

-----------------------------------
# Requirements
* Python 3 + MSVCRT
* GETCH() - 
This project is designed to run on a Windows machine, since MSVCRT is used.
If you desire to use this on a Linux machine, you need to install "getch" from this [pip package](https://pypi.org/project/getch/)
Alternatively, you may use the command: ```pip install getch```

* KBHIT() - 
You may use via [this code](https://www.mail-archive.com/linux-il@cs.huji.ac.il/msg66473.html) or [this gist](https://gist.github.com/michelbl/efda48b19d3e587685e3441a74457024)

-----------------------
# User Guide
* Clone this repo by using `https://github.com/aihsa1/MultiUserCHAT.git`
* `cd` into the folder

# Server
* run the server: `python server.py`
## Server Commands
```
p Prints a list of the connected clients
q Shuts down the server
a Shows admins
c Clears the screen
l Prints the list of command
```
# Client
run the client: `python client.py --name YOUR-NAME --ip DST-IP`

\* A valid name cannot contain ```@```, ```whitespaces```, nor ```!```

\* The default IP is Localhost ```(127.0.0.1)```
## Client Commands
* public message - type the message - ```->Hello World!```
* private message - add an exclamation mark + dst username before your message - ```->!USERNAME MSG```
* view admins - ```->view-managers```
* quitting the chat room - ```->quit```

## Admin Commands
* mute a user - ```->shsh USERNAME```
* kick out a user - ```->getout USERNAME```
* make a user an admin - ```->inviteMan USERNAME```


----------------------
# Notes
* This code has not been made user-friendly on purpose, as it has been developed as an exercise.
* Have fun :)
