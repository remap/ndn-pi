ndn-pi
======

Make sure you've already done:
export PYTHONPATH=$PYTHONPATH:<PyNDN root>/python

On producer/pir pi:
nfd-start
nfdc register / udp://192.168.1.5
python test_publish_async_ss.py

On consumer/cec pi:
nfd-start
nfdc register / udp://192.168.1.4
python test_get_async_ss.py
