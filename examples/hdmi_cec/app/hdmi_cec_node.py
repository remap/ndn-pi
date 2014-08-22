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
# TODO: NFD hack: uncomment once NFD forwarding fixed
# from app.discoveree import Discoveree
# TODO: NFD hack: remove once NFD forwarding fixed
from app.local_discoveree import LocalDiscoveree
from app.cec_tv import CecTv
try:
    import asyncio
except ImportError:
    import trollius as asyncio
import logging
logging.basicConfig(level=logging.INFO)

def main():
    loop = asyncio.get_event_loop()
    face = ThreadsafeFace(loop, "localhost")
    keyChain = KeyChain()
    face.setCommandSigningInfo(keyChain, keyChain.getDefaultCertificateName())

    # TODO: NFD hack: uncomment once NFD forwarding fixed
    # discoveree = Discoveree(loop, face, keyChain)
    # TODO: NFD hack: remove once NFD forwarding fixed
    discoveree = LocalDiscoveree(loop, face, keyChain)

    cecTv = CecTv(loop, face, keyChain, discoveree)

    loop.run_forever()
    face.shutdown()

if __name__ == "__main__":
    main()
