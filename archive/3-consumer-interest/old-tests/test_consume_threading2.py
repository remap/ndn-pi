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
from pyndn import Exclude
from pyndn import Face

from threading import Thread, Event
import sys
import json

face = Face("localhost")
statuses = { "00000000d1f2533912" : {} }
exclude = Exclude()

def onData(interest, data):
    global exclude
    print "Received data:", data.getName().toUri(),
    print "content:", data.getContent().toRawStr()
    pirSerial = data.getName().get(2)
    timeComponent = data.getName().get(3)
    payload = json.loads(data.getContent().toRawStr())
    statuses[pirSerial.toEscapedString()][int(timeComponent.toEscapedString())] = payload["pir"]
    if not exclude.matches(timeComponent):
        exclude.appendComponent(timeComponent)

def onTimeout(interest):
    print "Time out for interest", interest.getName().toUri()

class ExpressInterestThread(Thread):
    def __init__(self, event, face):
        Thread.__init__(self)
        self._stopped = event
        self._face = face
        self._count = 0

    def run(self):
        #global exclude
        while not self._stopped.wait(0.25): # TODO: make 0.25 # .wait(0.25)
            interest = Interest(Name("/home/pir/00000000d1f2533912"))
            # interest.setExclude(exclude)
            interest.setInterestLifetimeMilliseconds(2000.0)
            print "Send interest:", interest.getName().toUri(),
            print "exclude:", interest.getExclude().toUri()
            self._face.expressInterest(interest, onData, onTimeout)
            self._count += 1

stopFlag = Event()
thread = ExpressInterestThread(stopFlag, face)
thread.start()

try:
    while True:
        face.processEvents()
        time.sleep(0.01)
except:
    stopFlag.set()
    face.shutdown()
    raise
