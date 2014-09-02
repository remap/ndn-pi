Named Data Network Internet of Things Toolkit (NDN-IOTT)
==========================

 Getting Started
---------------------------------

The major components of this kit are:
-	PyNDN: a Python implementation of NDN
-	nfd: the NDN Forwarding Daemon, which manages connections (faces)
-   nrd: the NDN Routing Daemon, which routes interests and data 
-	ndn-config: a command-line utility for setting up new node types

There are other libraries included for further exploration of NDN:
-   repo-ng: a data repository server
-   ndn-cpp: C++ implementation of NDN
-   ndn-cxx: C++ implementation of NDN with eXperimental eXtensions



### Network Connectivity

In order to communicate using NDN, it is strongly recommended that all devices, Raspberry Pi or otherwise, be
connected to the same LAN. By default, Raspberry Pis are configured to create or join
a WiFi network named 'Raspi\_NDN' if a wireless interface is available. Alternatively, you may
 connect your Raspberry Pis by Ethernet.    


### Network Configuration

The basic unit of the IoT toolkit network is a node. Nodes are virtual, in that one
machine may host multiple simple nodes instead of one multi-purpose node. Although the functions of a node are
completely up to the user, we recommend using each node to group related commands. For example, a Raspberry Pi
with both LEDs and infrared sensors may run one node that responds to LED control commands, and another that 
reports proximity readings from the IR sensors.    

There is one special node type, the controller. Each network must have a controller. Its primary responsibilities 
are creating network certificates for all other nodes in the network, and maintaining a list of available 
services.    

### Node Configuration with ndn-config

Nodes must be configured with their network setup and command list by running the 
`ndn-config` utility. This utility prepares network certificates for the node, sets the node 
name, network prefix and controller's name, and adds commands to be broadcast to all other nodes
through the controller. The available settings are described below.

#### Edit network name settings
This is where a node is configured with the network prefix, its network name and the controller name. 
If either the network prefix or the controller name is misconfigured, the node will not be able to 
receive a certificate and will not start running its commands. All nodes with the same network prefix
 and the same controller name will be able to issue signed commands to each other.    

Your node prefix will appear on the network as the network prefix and node name joined. For example,
 if your network name is '/home' and your node name is 'mynode', the full network name associated 
with that node will be '/home/mynode'. There is no restriction to the number of nodes with the same 
name, but there is also no guarantee of the order in which they respond to commands.   

Since NDN names are hierarchical, you may also have node names like  '/home/mynode/' and '/home/mynode/sub' in the same network.
However, you may need to override `unknownCommandResponse` in your node subclasses to prevent the node
 with the higher-level name from intercepting commands sent to the sub-name.
     
To create a controller's configuration file, simply enter the same name for the node and the controller. This configuration file can then be used by running

        python -m ndn_pi.iot_controller <configuration file>

**Note**: commands set on a controller node are currently ignored and do not show up in the network 
name listing.

#### Edit command list
Here, you may set up commands that other nodes will be able to issue to this node. In order to support
commands, you will need to create a subclass of IotNode and implement the command handling functions.

You may add, edit, or delete commands. 'Add' and 'Edit' will take you to the command editor,
 where you may set the following attributes for the command:

* **Name**: the network name for the command. This will be visible to other nodes as a suffix added 
to your node name. For example, a command called 'setTimer' on a node named '/home/mynode' will
appear in the node listing as '/home/mynode/setTimer'.  
 Since names are hierarchical, you may also enter command names like 'setLight/18', as in the led\_control example in examples/.

* **Function name**: The name of a method on your IotNode subclass that will be called when the command is
received. 

 The method must take one argument, the command interest that was received, and return a Data object. An example method might be:
```python
    def myCommand(self, interest):
        doSomethingElse()
        replyData = pyndn.Data(interest.getName())
        replyData.setContent("OK")
        return replyData
```
 
 You must return a Data object from your method; even in the case where the command is not an explicit
 request for data, e.g. turning lights on, it is still necessary to send an acknowledgement 
of some kind back to the sender.

* **Keywords**: This is a comma separated list of keywords that should be associated with the command. They
may also be referred to as 'capabilities'. These are used as keys into the listing provided by 
the controller's `listDevices` command, so that nodes can find other nodes based on capability rather
 than by name. For example, in the led\_control example, the viewer node searches for nodes with the 
'led' capability and presents them in a list to the user.

* **Requires authentication**: This indicates whether the command must be signed by a node in the network
for it to be recognised. By default, commands do not require signing, meaning that any application with
access to the network may access the command. You can turn this on or off using the 'Toggle signed' button.
 

#### Regenerate node certificate

If you select this menu option, the ndnsec tool will be used to generate a fresh set of credentials for
the node name, whether there were existing certificates or not.

### Running Your Iot Nodes

If nfd is not running, start it by typing

        nfd-start

If you are using multiple Raspberry Pis, they must all be connected to the same network, whether by WiFi 
or Ethernet. This allows interests and data to be multicast to the other nodes over UDP. To set up multicast,
you must register your network name on an NDN multicast face.

If the Raspberry Pi is connected to only one network, you may simply use:

        nfdc register /home 2

If you change the network prefix in the configuration files, you need to register your new network prefix instead.    

If the Raspberry Pi has multiple network interfaces, you will need to use the 
'nfd-status' command to determine the correct face to register. Run

        nfd-status -f

and look for lines containing `remote=udp4://224.0.23.170:56363`. Find the faceid
 that contains an IP address on the IoT network. For example, if your nodes are all on a WiFi network, and your 
WiFi IP address is 192.168.16.7, you may find a line
that reads

        faceid=3 remote=udp4://224.0.23.170:56363 local=udp4://192.168.16.7:56356 ...

You should then register the network prefix using

        nfdc register /home 3

**Note:** Although multiple nodes may run on a single Raspberry Pi, the traffic from three or more nodes may be
too much, depending on the model of the Pi.

### Examples

This toolkit contains three examples that demonstrate common node and network setups.
-	led\_control:	Control LEDs connected to the general purpose input/output (GPIO) pins over the network
-	hdmi\_cec: 	Turn a CEC-enabled device on or off depending on room occupancy
-	content\_store: Save sensor readings for analysis or logging in a MemoryContentCache object

Try running these examples and going through the tutorial [TUTORIAL.md](TUTORIAL.md) to learn how nodes work together.

Note: In order to access the GPIO pins, an IotNode must be run as root.


Writing IoT Nodes
----------------


### Provided Classes
There are several classes provided as part of the Internet of Things toolkit for NDN. 
#### IotNode

Nodes in your network will generally be subclasses of IotNode. Besides adding methods for
interest handling (see ['Edit command list'](#edit-command-list) above), the following
methods may also be overridden:

* setupComplete 
```python
    def setupComplete(self)
```
  This method does nothing by default. It is called once the node has received its network
certificate from the controller and sent its capabilities list. This is the recommended
place for customized node behavior, e.g. searching for other nodes, scheduling tasks,
setting up custom callbacks.
  
* unknownCommandResponse
```python
    #returns pyndn.Data or None
    def unknownCommandResponse(self, interest)
```
   By default, this method composes an error message and adds 'unknown' to the end of the
interest name. You may return `None` to silently ignore the unknown interest, or perform
your own specialized handling of the interest and return a Data packet.


Other useful methods are:

* verificationFailed
```python
    def verificationFailed(self, dataOrInterest)
```
   Called when a command interest fails verification. The most common reasons for failing verification are invalid signatures, and unsigned interests being sent when signed interests are expected. The default implementation logs the failure.

* getSerial
```python
    def getSerial(self)
```
   Reads the Raspberry Pi serial number from /proc/cpuinfo. Useful if you need some 
identifier to distinguish Raspberry Pis with the same node name.

------

The remaining classes do not need to be subclassed, and it is not recommended that you modify them
 before you are comfortable with NDN security management. For more information, see [NDN Resources](#ndn-resources).

#### IotController

#### IotConsole

#### IotPolicyManager

#### IotIdentityStorage

NDN Resources
-----------------

* [NDN Common Client Libraries](http://named-data.net/doc/ndn-ccl-api/) for documentation of the classes available in PyNDN
* [ndn-cxx wiki](http://redmine.named-data.net/projects/ndn-cxx/wiki) for security information
* [NFD wiki](http://redmine.named-data.net/projects/nfd/wiki) for more on the internals of NDN packetsand forwarding

