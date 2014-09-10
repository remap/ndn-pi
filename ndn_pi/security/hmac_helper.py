# -*- Mode:python; c-file-style:"gnu"; indent-tabs-mode:nil -*- */
#
# Copyright (C) 2014 Regents of the University of California.
# Author: Adeola Bannis <thecodemaiden@gmail.com>
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
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
from pyndn.encoding import WireFormat
from pyndn.util import Blob
from sha256_hmac_signature import Sha256HmacSignature
from pyndn import Data, KeyLocatorType, Interest, Name
from hashlib import sha256
from random import SystemRandom
from time import time as timestamp

import hmac

class HmacHelper(object):
    def __init__(self, raw_key, wireFormat=None):
        super(HmacHelper, self).__init__()
        self.key = sha256(raw_key).digest()
        self.random = SystemRandom()
        if wireFormat is None:
            self.wireFormat = WireFormat.getDefaultWireFormat()
        else:
            self.wireFormat = wireFormat

    def signData(self, data):
        s = Sha256HmacSignature()
        data.setSignature(s)
        encoded = self.wireFormat.encodeData(data)[0]
        signer = hmac.new(self.key, bytearray(encoded.buf()), sha256)
        s.getKeyLocator().setType(KeyLocatorType.KEY_LOCATOR_DIGEST)
        s.getKeyLocator().setKeyData(signer.digest())
        data.setSignature(s)
     
    def verifyData(self, data):
        # clear out old signature so encoding does not include it
        savedSig = data.getSignature()
        data.setSignature(Sha256HmacSignature())

        encoded = self.wireFormat.encodeData(data)[0]
        hasher = hmac.new(self.key, bytearray(encoded.buf()), sha256)
        sig = savedSig.getKeyLocator().getKeyData()
        return sig.toRawStr() == hasher.digest()

    def signInterest(self, interest):
        # creates a nonce and timestamp - not exactly the same as a regular signed interest
        # because it is missing the SignatureInfo component
        nonceValue = bytearray(8)
        for i in range(8):
            nonceValue[i] = self.random.randint(0,0xff)
        timestampValue = bytearray(8)
        ts = int(timestamp()*1000)
        for i in range(8):
            byte = ts & 0xff
            timestampValue[-(i+1)] = byte
            ts = ts >> 8

        interestName = interest.getName()
        interestName.append(nonceValue).append(timestampValue)
        interest.setNonce(Blob(nonceValue))
        encoded = self.wireFormat.encodeInterest(interest)[0]
        hasher = hmac.new(self.key, bytearray(encoded.buf()), sha256)
        interestName.append(bytearray(hasher.digest()))
        interest.setNonce(Blob(nonceValue))

    def verifyInterest(self, interest):
        tempInterest = Interest(interest)
        oldNonce = interest.getNonce()
        sigComponent = interest.getName().get(-1)
        signedPortion = interest.getName().getPrefix(-1)
        tempInterest.setName(signedPortion)
        tempInterest.setNonce(oldNonce)
        encoded = self.wireFormat.encodeInterest(tempInterest)[0]
        hasher = hmac.new(self.key, bytearray(encoded.buf()), sha256)
        
        return sigComponent.getValue().toRawStr() == hasher.digest()


#if __name__ == '__main__':
#    h = HmacHelper('telly') 
#    i = Interest(Name('/my/name/is/hans'))
#    h.signInterest(i)
#    h.verifyInterest(i)

