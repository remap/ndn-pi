LED Control Network
===================


This example demonstrates three node types that make up a simple IoT network. 

Node Types
----------

###Controller

The controller in this network has no special function: it listens for certificate requests and directory requests.

###LED Node
    
This node directly controls LEDs using the GPIO pins. It listens for 
authorised (digitally signed) commands from other nodes in the network.

###Viewer Node
This node periodically asks the controller for a device listing, and presents
a menu to the user allowing her to issue 'on' or 'off' commands to any node that
offers an 'led' capability. 


Setup
-------

You may run these three nodes on one or more Raspberry Pis. The Raspberry Pi
 running the LED node expects to have an LED connected to BCM pin 24.     

<Insert wiring diagram?>
      
See the README.md in <ndn-pi path> for NDN setup steps.    

Running the Example
-------------------

The controller node should be started first, using:
        ./iot_controller.py 

Then the led node can be run using:
        sudo ./led_node.py 

And the viewer node can be run using:
        ./viewer_node.py 

Only the viewer node is directly interactive. It presents a list of nodes on the
 network offering the 'led' capability, which can be refreshed by pressing Enter.
The light on the LED node can be turned on and off using the menu. 
