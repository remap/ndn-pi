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

def sign():
    signature = hash data, timestamp, random number, AND secret barcode
    append signature to message

def onDataDevInit(interest, data):
    pass
    # verify data is signed by barcode
    data.getContent()
    # sign content (device's pub key) by gw-priv-key
    # publish to local repo

def onTimeout(interest):
    pass
    # resend interest once or twice?

# Some of these function args are probably not necessary
def onInterest(prefix, interest, transport, registeredPrefixId):
    # if interest.getName() matches "/home/gw/<serial>/<auth>"
        # do we have to verify interest signature?
        data = Data(Name("/home/gw/<serial>/<auth>"))
        data.setContent(public key)
        # send data

def onRegisterFailed(prefix):
    pass
    # try, try again

# generate root key
# name either "/home" or "/home/gw/<serial>"
# or maybe generate both (if we want multiple gateways, generate /home and /home/gw/<serial> and sign that by /home)
# then other gateways could get /home from first gateway

face = Face("localhost")
prefix = Name("/home/gw").append(serial)
face.registerPrefix(prefix, onInterest, onRegisterFailed)

# wait for device to come online
# HOW? Wait 30 sec?
# assume device already online
# receive barcode
# HOW? Wait for pipe? when you want to start a new device, run a program with barcode as arg

interest = Interest(Name("/home/dev").append(serial).append(<auth>))
# sign interest by barcode, can't use makeCommandInterest because that's async
face.expressInterest(interest, onDataDevInit, onTimeout)

# listen for <prefix> (will come from gateway)

