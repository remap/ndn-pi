#!/usr/bin/python
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

from pyndn import Name
from pyndn import Data
from sensors.pir import Pir
from util.common import Common
import time
import json
try:
    import asyncio
except ImportError:
    import trollius as asyncio

from ndn_pi.iot_node import IotNode
import logging

class PirPublisher(IotNode):
    def __init__(self):
        super(PirPublisher, self).__init__()

        # find the pins to set up from the config
        pinList = [18, 25]

        self._pirs = {}
        for pin in pinList:
            readCommand = Name('read').append(str(pin))
            self.addCommand(readCommand, self.onReadPir, ['pir'], False)
            pir = Pir(pin)
            self._pirs[pin] = {"device":pir, "lastVal":pir.read(), "lastTime":int(time.time()*1000)}

        self._count = 0

    def onReadPir(self, interest):
        # try to find a matching pir
        pirInfo = next((pair[1] for pair in self._pirs.items() 
            if Name(pair[1]["device"]).match(interest.getName())), None)

        if pirInfo is None:
            data = Data(interest.getName())
            data.setContent("MALFORMED COMMAND")
            data.getMetaInfo().setFreshnessPeriod(1000) # 1 second, in milliseconds
            return data

        lastTime = pirInfo["lastTime"]
        lastValue = pirInfo["lastVal"]

        # If interest exclude doesn't match timestamp from last tx'ed data
        # then resend data
        if not interest.getExclude().matches(Name.Component(str(lastTime))):
            print "Received interest without exclude ACK:", interest.getExclude().toUri()
            print "\tprevious timestamp:", str(lastTime)

            data = Data(Name(interest.getName()).append(str(lastTime)))
            payload = { "pir" : lastValue}
            content = json.dumps(payload)
            data.setContent(content)

            data.getMetaInfo().setFreshnessPeriod(1000) # 1 second, in milliseconds

            print "Sent data:", data.getName().toUri(), "with content", content
            return data

        # otherwise, make new data
        currentValue = pirInfo["device"].read()
        timestamp = int(time.time() * 1000) # in milliseconds
        pirInfo["lastTime"] = timestamp
        pirInfo["lastVal"] = currentValue

        data = Data(Name(interest.getName()).append(str(timestamp)))

        payload = { "pir" : currentValue}
        content = json.dumps(payload)
        data.setContent(content)

        data.getMetaInfo().setFreshnessPeriod(1000) # 1 second, in milliseconds

        print "Sent data:", data.getName().toUri(), "with content", content
        return data


if __name__ == '__main__':
    node = PirPublisher()
    node.start()
