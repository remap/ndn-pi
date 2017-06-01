Named Data Network Internet of Things Toolkit (NDN-IoTT)
==========================

 ***
 Update: Due to a lot of recent interest in this toolkit, there is now [a form here](https://goo.gl/forms/WDTG0Xtx2OT4KL0h1) for anyone who is running into difficulties installing or using ndn-pi. Based on the responses, we may update the project.
 ***
 
 Getting Started
---------------------------------

The major components of this kit are:
-	PyNDN: a Python implementation of NDN
-	nfd: the NDN Forwarding Daemon, which manages connections (faces)
-   nrd: the NDN Routing Daemon, which routes interests and data 

There are other libraries included for further exploration of NDN:
-   repo-ng: a data repository server
-   ndn-cpp: C++ implementation of NDN
-   ndn-cxx: C++ implementation of NDN with eXperimental eXtensions

### Network Connectivity

In order to communicate using NDN, all devices, Raspberry Pi or otherwise, must be
connected to the same LAN. By default, Raspberry Pis are configured to create or join
a WiFi network named 'Raspi\_NDN' if a wireless interface is available. 

The default password for 'Raspi\_NDN' is 'defaultpasswd'. It can be changed with the ndn-wifi-passwd tool,
or by modifying /etc/hostapd/hostapd.conf and /etc/wpa_supplicant/wpa_supplicant.conf.

Alternatively, you may connect your Raspberry Pis by Ethernet.    

### Network Configuration

If you are using multiple Raspberry Pis, they must all be connected to the same network, whether by WiFi 
or Ethernet. This allows interests and data to be multicast to the other nodes over UDP. To set up multicast,
you must register your network an NDN multicast face.

There is an installed script, ndn-iot-start, that will start the NDN forwarder and router if they are not 
already running, and automatically route traffic from your nodes to the multicast face. It assumes that your 
Pis are connected to a WiFi network, using the 'wlan0' interface. If you are using a different interface, e.g.
'eth0' for ethernet, you may run

        ndn-iot-start -i eth0

replacing 'eth0' with the desired interface name. For a list of network interfaces on your Pi, run 'ifconfig'.

If you wish to configure routing yourself **(not recommended)**, see [below](#manually-configuring-routing).


### Running Your Iot Nodes

The basic unit of the IoT toolkit network is a node. Nodes are virtual, in that one
machine may host multiple simple nodes instead of one multi-purpose node. Although the functions of a node are
completely up to the user, we recommend using each node to group related commands. For example, a Raspberry Pi
with both LEDs and infrared sensors may run one node that responds to LED control commands, and another that 
reports proximity readings from the IR sensors.    

There is one special node type, the controller. Each network must have a controller. Its primary responsibilities 
are creating network certificates for all other nodes in the network, and maintaining a list of available 
services. 

The configuration for the controller consists of just the network name (default is '/home') and the controller name
(default is 'controller'). The default configuration file can be in /home/pi/.ndn/controller.conf. To change controller settings, you
may edit this file, or run the included ndn-iot-controller script:

        ndn-iot-controller <network-name> <controller-name>

When nodes other than the controller join the network, they must be added by the user, by providing a serial number and
PIN. This prevents unknown machines from gaining access to protected network commands. Use the menu provided by the controller to pair the new
node by entering 'P'. You will be prompted for the serial, PIN and a new name for your node. After a few seconds, the node will 
finish its setup handshake with the controller and be ready to interact with the other nodes. You can use 'D' for 'directory' to
see the commands available on the new node.

**Note:** Although multiple nodes may run on a single Raspberry Pi, the traffic from three or more nodes slow nfd down
considerably, depending on the model of the Pi.

**Note:** The directory may not correctly reflect the presence of multiple nodes with the same name. This limitation should be fixed in later
versions.

### Examples

This toolkit contains three examples that demonstrate common node and network setups.
-	led\_control:	Control LEDs connected to the general purpose input/output (GPIO) pins over the network
-	hdmi\_cec: 	Turn a CEC-enabled device on or off depending on room occupancy
-	content\_store: Save device statistics in a MemoryContentCache object for later analysis or logging 

Try running these examples and going through the tutorial [TUTORIAL.md](TUTORIAL.md) to learn how nodes work together.

**Note: In order to access the GPIO pins, an IotNode must be run as root.**

### Manually configuring routing

It is recommended that you use the included script, ndn-iot-start, but you can manually set up routing on your nodes with the following
steps.

1. Ensure that the Raspberry Pi is connected to the network (wired or wireless) that will host your IoT network.

2. Start the NDN forwarder and router by running
        
        nfd-start

3. Tell the forwarder to route network traffic to the multicast face.
 If you are using WiFi only with your Raspberry Pi, the multicast face will typically have faceid 2. Otherwise, 
 you will need to use the 'nfd-status' command to determine the correct face to register. Run

        nfd-status -f

 and look for lines containing `remote=udp4://224.0.23.170:56363`. Find the faceid
 that contains an IP address on the IoT network. For example, if your nodes are all on a WiFi network, and your
 WiFi IP address is 192.168.16.7, you may find a line that reads

        faceid=3 remote=udp4://224.0.23.170:56363 local=udp4://192.168.16.7:56356 ...

4. Tell the forwarder to route traffic to the face you discovered in *3*.

        nfdc-register / <faceid>


Writing IoT Nodes
----------------


### Provided Classes
There are several classes provided as part of the Internet of Things toolkit for NDN. 
#### IotNode

Nodes in your network will generally be subclasses of IotNode. 

The most important method for customizing nodes is `addCommand`:

```python
    def addCommand(suffix, func, keywords, isSigned)
```
 This is used to register your custom interest handling methods. The parameters are:
 - `suffix`: An NDN name that will be added to the node prefix to form the full command name.
 - `func`: A function that is called whenever the node receives an interest matching the suffix. The
    function must take an Interest object and return a Data object:

     ```python
         # returns pyndn.Data or None
         def handlerFunction(interest):
             dataName = Name(interest.getName())
             # ... do some processing based on the interest
             # return a Data object or the interest will time out
             response = Data(dataName)
             response.setContent('Done')
             return response
     ```
     Note that the sender of the interest will not receive your reply if the name of the data object does not match
     the interest name. That is, you may append components to `dataName`, but not remove them. You may also return `None`,
     which will cause the interest to time out.

 - `keywords`: A list of strings. The controller groups together all commands that share a keyword, so that other nodes
     can search for a particular capability, service, sensor type, etc. You are free to define as many keywords as you like,
     and their meaning is mainly application-dependent.
 - `isSigned`: By default, this is set to `False`. Setting this to `True` will allow only devices who are part of your network to
     invoke the command, by signing their command interests.

Besides adding methods for interest handling with `addCommand`, nodes can be further customized by overriding the
following methods:

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

* verificationFailed
```python
    def verificationFailed(self, dataOrInterest)
```
   Called when a command interest fails verification. The most common reasons for failing verification are invalid signatures, 
and unsigned interests being sent when signed interests are expected. The default implementation logs the failure.

* getSerial
```python
    def getSerial(self)
```
   Reads the Raspberry Pi serial number from /proc/cpuinfo. You may override this to provide some other unique id for your
Raspberry Pis or even individual IotNodes.

------

The remaining classes do not need to be subclassed, and it is not recommended that you modify them
 before you are comfortable with the toolkit and with  NDN security management. For more information, 
see [NDN Resources](#ndn-resources).

#### IoT Network Classes

* BaseNode
* IotController
* IotConsole

#### Security Classes
* HmacHelper
* IotPolicyManager
* IotIdentityManager
* IotIdentityStorage
* IotPrivateKeyStorage

NDN Resources
-----------------

* [NDN Common Client Libraries](http://named-data.net/doc/ndn-ccl-api/) for documentation of the classes available in PyNDN
* [ndn-cxx wiki](http://redmine.named-data.net/projects/ndn-cxx/wiki) for security information
* [NFD wiki](http://redmine.named-data.net/projects/nfd/wiki) for more on the internals of NDN packets and forwarding

