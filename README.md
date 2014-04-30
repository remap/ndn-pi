ndn-pi
======

Make sure you've already done:
export PYTHONPATH=$PYTHONPATH:<PyNDN root>/python

On consumer/cec pi:
nfd-start
./nfd_add_host.sh 192.168.1.4

On producer/pir pi:
nfd-start
./nfd_add_host.sh 192.168.1.5
python test_publish_async_ss.py

On consumer/cec pi:
python test_get_async_ss.py
