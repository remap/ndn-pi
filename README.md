ndn-pi
======

Prerequisites
-------------
Required: Python 2.7 or later
Required: [NFD](https://github.com/named-data/NFD)
Required: [PyNDN2](https://github.com/named-data/PyNDN2)
Required: trollius (for asyncio in Python 2.7)
Required: [libcec](https://github.com/Pulse-Eight/libcec)

Running
---
Make sure you've already done:
   export PYTHONPATH=$PYTHONPATH:<PyNDN root>/python

On pir pi:
  nfd-start
  nfdc register /home 2
  sudo python app/occupancy_node_1.py

On consumer/cec pi:
  nfd-start
  nfdc register /home 3
  python app/hdmi_cec_node.py (either in separate terminal or background)
  python app/consumer.py

Note about nfdc register command
<faceId> is the udp multicast face, which can be attained via nfd-status - it's the line with udp4://224.0.23.170:56363
For the gateway, it's 3
For non-gateways, it's 2
