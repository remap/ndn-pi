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

import time
from pyndn import Name
from pyndn import Interest
from pyndn import Face
from pyndn.security import KeyChain

def onInterest(prefix, interest, transport, registeredPrefixId):
    print "Got interest for", interest.getName().toUri(), "at prefix", prefix.toUri()

def onRegisterFailed(prefix):
    print "Register failed for prefix", prefix.toUri()

face = Face("localhost")
keyChain = KeyChain()
face.setCommandSigningInfo(keyChain, keyChain.getDefaultCertificateName())

face.registerPrefix(Name("/home/1"), onInterest, onRegisterFailed)
face.registerPrefix(Name("/home/2"), onInterest, onRegisterFailed)
face.registerPrefix(Name("/home/3"), onInterest, onRegisterFailed)
face.registerPrefix(Name("/home/4"), onInterest, onRegisterFailed)
face.registerPrefix(Name("/home/5"), onInterest, onRegisterFailed)

while True:
    face.processEvents()
    time.sleep(0.01)    
