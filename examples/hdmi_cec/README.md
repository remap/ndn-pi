HDMI-CEC TV controller
======================


This network reads any available passive infrared sensors (PIRs) to determine room occupancy.
It turns connected TVs off if all sensors report no occupancy, and turns TVs on if more than 2
nodes report occupancy.

Node Types
----------

###Controller

The controller in this network has no special function: it listens for certificate requests and device listing requests.

###PIR Publisher Node

This node handles requests for PIR status by reading PIRs attached to the GPIO pins (by default 25 and 18).

###CEC TV Node

This node sends commands to a CEC-enabled device attached to the HDMI output of the Raspberry Pi.

### Consumer Node
This node searches for nodes with 'pir' and 'cec' capabilities. It periodically reads the status of all PIR sensors,
and issues commands to the TV.

Setup
-------

### PIR Publisher
This node expects two passive infrared sensors connected to pins 25 and 18. The number and placement of PIR sensors
can be changed by editing 'pir.conf' with `ndn-config`.

<Insert wiring diagram?>

### CEC TV Node
This node expects to be connected to an HDMI-CEC enabled television/monitor.

### Network Setup      
See the README.md in (ndn-pi path?) for NDN setup steps.    

Running the Example
-------------------

The controller node should be started first, using:

        python -m ndn_pi.iot_controller &

The CEC controller and PIR publisher nodes require root access:

        sudo -E ./cec_tv.py cec_tv.conf &

and

	    sudo -E ./pir_publisher.py pir.conf &


The consumer can be run using
        
        ./consumer.py consumer.conf&

