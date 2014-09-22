LED Control Network
===================


This example demonstrates three node types that make up a simple IoT network. 

Node Types
----------

###Controller

The controller in this network has no special function: it listens for certificate requests and device listing requests.

###LED Node
    
This node directly controls an LED attached to a GPIO pin (by default, 24).

### Multi-LED Node
This is a more customizable version of the LED node. It separately controls LEDs attached to the GPIO pins 
(by default, 17 and 24).

###User Node
This node periodically asks the controller for a device listing, and randomly sends an available LED command.

Setup
-------

### LED Node
This node expects to have an LED connected to GPIO pin 24 by default, but you can change the pin number by
specifying a different number on the command line. 

<Insert wiring diagram?>

### Multi-LED Node
This node expects to have LEDs connected to GPIO pins 17 and 24 by default. 

<Insert wiring diagram?>

### Network Setup      
See the top-level README.md in ndn-pi for NDN network setup steps.    

Running the Example
-------------------
The nodes can be started in any order, but the controller must be running to set up new nodes, using the 'P' option in the controller menu.
You can also use the 'D' option to see a listing of all commands available to the network. 

**Note**: If the controller goes down, nodes may keep running but will not be able to refresh their directories. Also, when the controller is
restarted, it may take a while to receive updates from already running nodes.

