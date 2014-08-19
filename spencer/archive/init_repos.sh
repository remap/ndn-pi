# Copyright (C) 2014 Regents of the University of California.
# Author: Spencer Sutterlin <ssutterlin1@ucla.edu>
# 
# This file is part of ndn-pi (Named Data Networking - Pi).
#
# ndn-pi is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
# A copy of the GNU General Public License is in the file COPYING.

sudo apt-get install build-essential
sudo apt-get install openssl expat libpcap-dev
sudo apt-get install libssl-dev libsqlite3-dev libcrypto++-dev libboost-all-dev

git clone https://github.com/named-data/ndnx.git
git clone https://github.com/named-data/ndn-cpp.git
git clone https://github.com/named-data/PyNDN2.git

# Not needed on pi if cross-compiling
#git clone https://github.com/named-data/ndn-cxx.git
#git clone https://github.com/named-data/NFD.git
#git clone https://github.com/named-data/repo-ng.git

echo "export PYTHONPATH=$PYTHONPATH:$HOME/ndn/PyNDN2/python:$HOME/ndn/ndn-pi" >> ~/.bashrc
echo "ipv6" >> /etc/modules
