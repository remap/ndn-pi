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

from pyndn import ThreadsafeFace
from pyndn.security import KeyChain
from app.device_manager import DeviceManager
from app.consumer import Consumer
try:
    import asyncio
except ImportError:
    import trollius as asyncio
import logging
logging.basicConfig(level=logging.INFO)

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    face = ThreadsafeFace(loop, "localhost")
    keyChain = KeyChain()
    face.setCommandSigningInfo(keyChain, keyChain.getDefaultCertificateName())

    deviceManager = DeviceManager(loop, face, keyChain)
    consumer =  Consumer(loop, face, keyChain, deviceManager)

    face.stopWhen(lambda: consumer._callbackCountUniqueData >= 20)
    loop.call_soon(deviceManager.initDiscovery)
    loop.call_soon(consumer.expressInterestPirAndRepeat)
    loop.run_forever() # Run until stopWhen stops the loop
    face.shutdown()
