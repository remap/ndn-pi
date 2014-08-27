Internet of Things Toolkit
using
Named Data Network

0] Kit components
=================================

This kit contains the following libraries and utilities:
-	PyNDN: a Python implementation of NDN
-	nfd: the NDN Forwarding Daemon, which routes NDN traffic over IP
-	ndn-config: a command-line utility for setting up new node types


1] Network Connectivity
=================================
In order to communicate using NDN, it is strongly recommended that all devices, Raspberry Pi or otherwise, be
connected to the same LAN. By default, Raspberry Pis are configured to create or join
an ad-hoc network named 'Raspi\_NDN', but you are free to set up WiFi yourself. Alternatively, you may connect
your Raspberry Pis by Ethernet.    



2] Network Configuration
=================================
The basic unit of the IoT toolkit network is a node. Nodes are virtual, in that one
machine may host multiple simple nodes instead of one multipurpose node. Although the functions of a node are
completely up to the user, we recommend using each node to group related commands. For example, a Raspberry Pi
with both LEDs and infrared sensors may run one node that responds to LED control commands, and another that 
reports proximity readings from the IR sensors.

There is one 




3] IoT Configuration
=================================
Before you can run an IoT node on your Raspberry Pi, you must first run ndn-config to create a configuration file
for each node. Nodes are virtual



4] Examples
=================================
This toolkit contains three examples that demonstrate //?F./f
-	led\_control:	Control LEDs connected to the general purpose input/output (GPIO) pins over the network
-	hdmi\_cec\_: 	Turns a CEC-enabled device on or off depending on room occupancy
-	content\_cache: Save sensor readings for analysis or logging

In order to access the GPIO pins, an IotNode must be run as root

5] Writing your own IoT Nodes
=================================

