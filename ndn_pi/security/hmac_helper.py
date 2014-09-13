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

    @classmethod
    def generatePin(cls):
        """
        Generate a pin to be entered into another device.
        Restricting this to 8 bytes (16 hex chars) for now.
        """
        pin = bytearray(8)
        random = SystemRandom()
        for i in range(8):
            pin[i] = random.randint(0,0xff)
        return str(pin).encode('hex')
    
    @classmethod
    def extractInterestSignature(cls, interest, wireFormat=None):
        if wireFormat is None:
            wireFormat = WireFormat.getDefaultWireFormat()

        try:
            signature = wireFormat.decodeSignatureInfoAndValue(
                            interest.getName().get(-2).getValue().buf(),
                            interest.getName().get(-1).getValue().buf())
        except:
            signature = None

        return signature

    def signData(self, data, keyName=None, wireFormat=None):
        data.setSignature(Sha256HmacSignature())
        s = data.getSignature()

        s.getKeyLocator().setType(KeyLocatorType.KEYNAME)
        s.getKeyLocator().setKeyName(keyName)

        if wireFormat is None:
            wireFormat = WireFormat.getDefaultWireFormat()
        encoded = data.wireEncode(wireFormat)
        signer = hmac.new(self.key, bytearray(encoded.toSignedBuffer()), sha256)
        s.setSignature(Blob(signer.digest()))
        data.wireEncode(wireFormat)
     
    def verifyData(self, data, wireFormat=None):
        # clear out old signature so encoding does not include it
        if wireFormat is None:
            wireFormat = WireFormat.getDefaultWireFormat()
        encoded = data.wireEncode(wireFormat)
        hasher = hmac.new(self.key, bytearray(encoded.toSignedBuffer()), sha256)
        sigBytes = data.getSignature().getSignature()
        return sigBytes.toRawStr() == hasher.digest()

    def signInterest(self, interest, keyName=None, wireFormat=None):
        # Adds the nonce and timestamp here, because there is no
        # 'makeCommandInterest' call for this yet
        nonceValue = bytearray(8)
        for i in range(8):
            nonceValue[i] = self.random.randint(0,0xff)
        timestampValue = bytearray(8)
        ts = int(timestamp()*1000)
        for i in range(8):
            byte = ts & 0xff
            timestampValue[-(i+1)] = byte
            ts = ts >> 8

        if wireFormat is None:
            wireFormat = WireFormat.getDefaultWireFormat()

        s = Sha256HmacSignature()
        s.getKeyLocator().setType(KeyLocatorType.KEYNAME)
        s.getKeyLocator().setKeyName(keyName)

        interestName = interest.getName()
        interestName.append(nonceValue).append(timestampValue)
        interestName.append(wireFormat.encodeSignatureInfo(s))
        interestName.append(Name.Component())

        encoding = interest.wireEncode(wireFormat)
        signer = hmac.new(self.key, encoding.toSignedBuffer(), sha256)

        s.setSignature(Blob(signer.digest()))
        interest.setName(interestName.getPrefix(-1).append(
            wireFormat.encodeSignatureValue(s)))


    def verifyInterest(self, interest, wireFormat=None):
        if wireFormat is None:
            wireFormat = WireFormat.getDefaultWireFormat()

        signature = self.extractInterestSignature(interest, wireFormat)
        encoding = interest.wireEncode(wireFormat)
        hasher = hmac.new(self.key, encoding.toSignedBuffer(), sha256)
        return signature.getSignature().toRawStr() == hasher.digest()

