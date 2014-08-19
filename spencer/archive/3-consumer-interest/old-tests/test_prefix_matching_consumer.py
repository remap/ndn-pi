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
from pyndn import Face

def onData(self, interest, data):
    print "onData"

def onTimeout(self, interest):
    print "onTimeout"

def main():
    face = Face("localhost")
    
    name0 = Name("/home")
    face.expressInterest(name0, onData, onTimeout)

    name1 = Name("/home/dev/cereal/")
    face.expressInterest(name1, onData, onTimeout)

    name2 = Name("/home/dev/cereal")
    face.expressInterest(name2, onData, onTimeout)

    name3 = Name("/home/dev/cereal/key")
    face.expressInterest(name3, onData, onTimeout)

    name4 = Name("/home/dev/cereal/0")
    face.expressInterest(name4, onData, onTimeout)

    name5 = Name("/home/dev/cereal/key/9")
    face.expressInterest(name5, onData, onTimeout)

    while True:
        face.processEvents()
        # We need to sleep for a few milliseconds so we don't use 100% of the CPU.
        time.sleep(0.01)    

    face.shutdown()

main()
