# UDP Robot Control System for Franka Robot

`sendcomm.py` is the server that will SEND the COMMand.

`getcomm_controlrob.py` is the server that will GET the COMMands from `sendcomm` and will CONTROL the ROBot.

just run `getcomm_controlrob.py` as is on the computer that controls the robot.

`sendcomm.py` right now will read in from a text file and give commands.
See how `main()` creates the `RobotController` as an example.