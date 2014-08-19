ndn-pi
======

Prerequisites
-------------
* Required: Python 2.7 or later
* Required: [NFD](https://github.com/named-data/NFD)
* Required: [PyNDN2](https://github.com/named-data/PyNDN2)
* Required: trollius (for asyncio in Python 2.7)
* Required: [libcec](https://github.com/Pulse-Eight/libcec)

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

Note about `nfdc register <prefix> <faceId>`:

`<faceId>` should be the udp multicast face, which can be attained via nfd-status - it's the line with `udp4://224.0.23.170:56363`

Typically, for the gateway (because it has 2 IP addresses), faceId=3, for non-gateways, faceId=2.

License
-------
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
A copy of the GNU General Public License is in the file COPYING.
