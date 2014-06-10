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

import asyncio
from pyndn import Name
from pyndn import Interest
from pyndn import Exclude
from pyndn import ThreadsafeFace

import logging
logging.basicConfig(filename="async.log", level=logging.INFO)

class Consumer(object):
    def __init__(self):
        self._callbackCount = 0
        self._stopped = False
        self._loop = asyncio.get_event_loop()
        self._face = ThreadsafeFace(self._loop, "localhost")
        self._exclude = Exclude()
        self._pirStatuses = {}

    def onData(self, interest, data):
        self._callbackCount += 1
        logging.info("Data: " + data.getName().toUri())
        logging.info("Content: " + data.getContent().toRawStr())
        timeComponent = data.getName().get(3)
        self._exclude.clear()
        self._exclude.appendAny()
        self._exclude.appendComponent(timeComponent)

    def onTimeout(self, interest):
        self._callbackCount += 1
        logging.info("Timeout interest: " + interest.getName().toUri())

    def express_interest_and_repeat(self, loop):
        logging.info("Counter's callbackCount: " + str(self._callbackCount))
        # Express interest here
        interest = Interest(Name("/home/pir/00000000d1f2533912"))
        interest.setExclude(self._exclude)
        interest.setInterestLifetimeMilliseconds(1000.0)
        interest.setChildSelector(1)
        logging.info("Send interest: " + interest.getName().toUri())
        logging.info("Exclude: " + interest.getExclude().toUri())
        self._face.expressInterest(interest, self.onData, self.onTimeout)
        loop.call_later(0.5, self.express_interest_and_repeat, loop)
        

    def run(self):
        self._face.stopWhen(lambda: self._callbackCount >= 100)
        self._loop.call_soon(self.express_interest_and_repeat, self._loop) # might need _threadsafe
        # Run until stopWhen stops the loop.
        self._loop.run_forever()
        self._face.shutdown()

if __name__ == "__main__":
    c = Consumer()
    c.run()
