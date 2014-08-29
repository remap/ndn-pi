
Content Publisher with Cache
============================


This example collects system information such as memory and CPU usage and stores them 
into a content cache for later retrieval.

Node Types
----------

###Controller

The controller in this network has no special function: it listens for certificate requests and device listing requests.

### Publisher Node
    
This node directly controls an LED attached to a GPIO pin (by default, 24).


Setup
-------

No special hardware setup is needed for this example.

### Network Setup      
See the README.md in (ndn-pi path?) for NDN setup steps.    

Running the Example
-------------------

The controller node should be started first, using:

        python -m ndn_pi.iot_controller &

Then the publisher can be started using

        ./publisher.py &

Finally, we run a console node using:

        python -m ndn_pi.iot_console &


The console node periodically polls the controller for available commands and presents them to the user. If
the publisher was started successfully, you should see an entry like:
```
repo:
    /home/repoman/listDataPrefixes
```

If you enter this as written (don't add any spaces!), you should receive a JSON list containing all
data prefixes that the repo is listening on. Right now, there is only one, `/home/repoman/data`.

If you now enter `/home/rempoman/data` into the console, you will receive the latest data from the content cache.
You will notice that the name of the data (after 'Received: ') is the interest name you provided with an extra
component at the end. If you wish to retreive the same data object in the future, you can send an interest with its
full name. Otherwise, the content cache will continue to return new data as it is created.
