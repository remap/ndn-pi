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

def onDataGWInit(interest, data):
    pass
    # verify data is signed by barcode
    # install as root of trust
    data.getContent()
    # How? Where? There's no repo running on these guys, do we just save to disk or use ndn-cxx ndnsec tools?
    # ndnsec-cert-install

def onTimeout(interest):
    pass
    # resend interest once or twice?

# device registers prefix, waits
# gateway initiates discovery, device responds with key
# this doesn't integrate perfectly with existing discovery code in occupancy_node
# because in existing disc. code, it responds with the attached devices
# whereas here it responds with key
# merge this and occupancy_node code
def onInterest(prefix, interest, transport, registeredPrefixId):
    # if interest.getName() matches "/home/dev/<dev-id>/<auth>"
        # do we have to verify interest signature?
        data = Data(Name("/home/dev/<dev-id>/<auth>"))
        data.setContent(public key)
        # send data
        interest = Interest(Name("/home/gw").append(<auth>))
        # sign interest by barcode
        face.expressInterest(interest, onDataGWInit, onTimeout)

def onRegisterFailed(prefix):
    pass
    # try, try again

# check for self keys
# if not keys, generate key for self
prefix = Name("/home/dev").append(<dev-id>)
face.registerPrefix(prefix, onInterest, onRegisterFailed)

# listen for <prefix> (will come from gateway)

