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

###Viewer Node
This node periodically asks the controller for a device listing, and presents
a menu to the user allowing her to issue 'on' or 'off' commands to any node that
offers an 'led' capability. 

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
See the README.md in (ndn-pi path?) for NDN setup steps.    

Running the Example
-------------------
The nodes can be started in any order. When each 
The controller node should be started first, using:

        python -m ndn_pi.iot_controller &

Then the led nodes can be run using:

        sudo -E ./led_node.py &

and
	    sudo -E ./led_multi_node.py &

Finally, we can run the viewer node using:

        ./viewer_node.py

Only the viewer node is user-interactive. It presents a list of nodes on the
 network offering the 'led' capability, which can be refreshed by pressing Enter.
The light on the LED nodes can be turned on and off using the menu. 
