Internet of Things Toolkit for NDN
==========================

 Getting Started
---------------------------------

The major components of this kit are:
-	PyNDN: a Python implementation of NDN
-	nfd: the NDN Forwarding Daemon, which routes NDN traffic over IP
-	ndn-config: a command-line utility for setting up new node types

There are other libraries included for further exploration of NDN:
-   repo-ng: a data repository server
-   ndn-cpp: C++ implementation of NDN
-   ndn-cxx: C++ implementation of NDN with eXperimental eXtensions



### Network Connectivity

In order to communicate using NDN, it is strongly recommended that all devices, Raspberry Pi or otherwise, be
connected to the same LAN. By default, Raspberry Pis are configured to create or join
a network named 'Raspi\_NDN' by default. Alternatively, you may connect your Raspberry Pis by Ethernet.    


### Network Configuration

The basic unit of the IoT toolkit network is a node. Nodes are virtual, in that one
machine may host multiple simple nodes instead of one multipurpose node. Although the functions of a node are
completely up to the user, we recommend using each node to group related commands. For example, a Raspberry Pi
with both LEDs and infrared sensors may run one node that responds to LED control commands, and another that 
reports proximity readings from the IR sensors.    

There is one special node type, the controller. Each network must have a controller. Its primary responsibilities 
are creating network certificates for all other nodes in the network, and maintaining a list of available 
services.    

Nodes must be configured with their network setup and command list by running the 
ndn-config utility. This utility prepares network certificates for the device as
well as setting the node name, network prefix and controller's name.      

See the tutorial for more information on network configuration using ndn-config.    

### Running Iot Nodes

If nfd is not running, start it by typing

        nfd-start

If you are using multiple Raspberry Pis, they must all be connected to the same network, whether by WiFi 
or Ethernet. This allows interests and data to be multicast to the other nodes over UDP. To set up multicast,
you must *register* your network name on an NDN multicast face.

If the Raspberry Pi is connected to only one network, you may simply use:

        nfdc register /home 2

If you change the network prefix in the configuration files, you need to register your new network prefix instead.    

If the Raspberry Pi has multiple network interfaces, you will need to use the 
'nfd-status' command to determine the correct face to register. Run

        nfd-status -f

and look for lines containing 'remote=udp4://224.0.23.170:56363'. Find the faceid
 that contains an IP address on the IoT network. For example, if your nodes are all on a WiFi network, and your 
WiFi IP address is 192.168.16.7, you may find a line
that reads

        faceid=3 remote=udp4://224.0.23.170:56363 local=udp4://192.168.16.7:56356 ...

You should then register the network prefix using

        nfdc register /home 

*Note:* Although multiple nodes may run on a single Raspberry Pi, the traffic from three or more nodes may be
too much, depending on the model of the Pi.

### Examples

This toolkit contains three examples that demonstrate common node and network setups.
-	led\_control:	Control LEDs connected to the general purpose input/output (GPIO) pins over the network
-	hdmi\_cec: 	Turn a CEC-enabled device on or off depending on room occupancy
-	content\_cache: Save sensor readings for analysis or logging in a MemoryContentCache or an NDN repository

Try running these examples and going through the tutorial [TUTORIAL.md] to learn how nodes work together.

Note: In order to access the GPIO pins, an IotNode must be run as root.


Advanced Users
--------------

###Provided Classes

There are several classes provided as part of the Internet of Things toolkit for NDN.
#### IotNode

This is the most important class for 
