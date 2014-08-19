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

# Configure NFD from samples
sudo cp /usr/local/etc/ndn/nfd.conf.sample /usr/local/etc/ndn/nfd.conf
sudo cp /usr/local/etc/ndn/client.conf.sample /usr/local/etc/ndn/client.conf

# Generate keys and establish root of trust
sudo mkdir -p /usr/local/etc/ndn/keys
ndnsec-keygen /`whoami` | ndnsec-install-cert -
ndnsec-cert-dump -i /`whoami` > default.ndncert
sudo mv default.ndncert /usr/local/etc/ndn/keys/default.ndncert

# Generate keys for app
#serial=`cat /proc/cpuinfo | grep "Serial" | awk -F":" '{print $2}' | tr -d ' '`
#ndnsec-keygen /home/dev/$serial | ndnsec-install-cert -
#ndnsec-cert-dump -i /home/dev/$serial | sudo ndnsec-install-cert - # Also install as root cert because sensor publisher must run as sudo
#ndnsec-cert-dump -i /home/dev/$serial > default.ndncert
#sudo mv default.ndncert /usr/local/etc/ndn/keys/default.ndncert

#ndnsec-set-default /pi
