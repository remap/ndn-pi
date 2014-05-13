ndn-pi
======

Make sure you've already done:
	export PYTHONPATH=$PYTHONPATH:<PyNDN root>/python

On producer/pir pi:
	nfd-start
	nfdc register /home 2
	ndn-repo-ng -c config/repo-ng.conf &
	sudo su
	export PYTHONPATH=$PYTHONPATH:<PyNDN2 root>/python:<ndn-pi root>
	python tests/publish_pir.py

On consumer/cec pi:
	nfd-start
	nfdc register /home 3
	python test_get_async_ss.py

Note about nfdc register command
<faceId> is the udp multicast face, which can be attained via nfd-status - it's the line with udp4://224.0.23.170:56363
For the gateway, it's 3
For non-gateways, it's 2
