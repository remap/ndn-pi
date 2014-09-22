
Named Data Network Internet of Things Toolkit (NDN-IOTT)
=======
Tutorial
=========

This tutorial will walk you through configuring and running your own IoT network over NDN.
Before following this tutorial, try running the 'led\_control' example in the examples folder.

Copy the 'led\_control' folder to a new location so you can make changes.
 
Extending the LED control example
-------------------------------------

### Adding LEDs
The easiest way to extend the LED control network is to add another node that provides the same type of service, controlling an LED. 
You may attach an LED to a different pin (e.g. pin 17), or run another node controlling the same pin. You may add this new node to
any Raspberry Pi in your network (including one already running an LED node).

To start the new node, run

        sudo ./led_node.py [pin]

with an optional pin number. If no pin number is given, 24 is assumed. After pairing the new node with the controller, enter 'D' 
in the controller menu. You will see new entries for the new node you have registered. Try sending interests
to turn the LED on and off.

Another way to extend the network is to add more LEDs to the multi-LED node. 
Open 'led_multi_node.py' and add another pin to the pinList. Save and run the 
new node with

        sudo ./led_multi_node.py

Now the controller directory should show three different pins available for control on the multi-LED node.

### Adding commands to existing nodes

You can also add commands to the nodes to increase their capabilities. Open up 'led\_node.py'. You will see there is an 'onBlinkCommand' 
method that is not currently used. This method toggles blinking on the controlled LED. To install this command,
add the following to the end of the __init__ method:

   ```python
        blinkCommand = Name('toggleBlink')
        self.addCommand(blinkCommand, self.onBlinkCommand, ['led', 'light'], False)
   ```

Now run the node and pair it with the controller as usual. You will now see the blink command
in the directory. Try sending interests to turn blinking on and off.

### Requiring signed commands

The final change you can make to a node is to require signing for its commands. Signed commands 
contain keys that can be used to determine the identity of the sender. To require signing, simply change the `False` at the end of the `addCommand` lines to `True`.

Now, when you run the node and pair with the controller, your commands will only be
successful if you choose to sign them. To sign commands sent in source code, you must call

    self.face.makeCommandInterest(interest)

just before expressing the interest.
