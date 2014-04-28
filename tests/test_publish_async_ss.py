# -*- Mode:python; c-file-style:"gnu"; indent-tabs-mode:nil -*- */
#
# Copyright (C) 2014 Regents of the University of California.
# Author: Jeff Thompson <jefft0@remap.ucla.edu>
# See COPYING for copyright and distribution information.
#

import time
from pyndn import Name
from pyndn import Data
from pyndn import Face
from pyndn.security import KeyType
from pyndn.security import KeyChain
from pyndn.security.identity import IdentityManager
from pyndn.security.identity import MemoryIdentityStorage
from pyndn.security.identity import MemoryPrivateKeyStorage
from pyndn.util import Blob

import subprocess
# from pir import readPir # TODO: include, run as root
from os.path import expanduser, join

with open(join(expanduser("~"), ".ssh", "id_rsa.pub")) as file:
    DEFAULT_PUBLIC_KEY_DER = bytearray(file.read())

with open(join(expanduser("~"), ".ssh", "id_rsa")) as file:
    DEFAULT_PRIVATE_KEY_DER = bytearray(file.read())

def dump(*list):
    result = ""
    for element in list:
        result += (element if type(element) is str else repr(element)) + " "
    print(result)

class Echo(object):
    def __init__(self, keyChain, certificateName):
        self._keyChain = keyChain
        self._certificateName = certificateName
        self._responseCount = 0
        
    def onInterest(self, prefix, interest, transport, registeredPrefixId):
        self._responseCount += 1

        # Make and sign a Data packet.
        data = Data(interest.getName())
        content = "Echo " + interest.getName().toUri()
        if interest.getName().getSubName(4).equals(Name("/temp")):
            temp = subprocess.check_output(["vcgencmd", "measure_temp"])
            content = time.strftime("%d %b, %Y %H:%M:%S") + temp
        elif interest.getName().getSubName(4).equals(Name("/pir")):
            pir = 'Insert pir status here' # TODO: readPir()
            content = time.strftime("%d %b, %Y %H:%M:%S") + pir
        data.setContent(content)
        self._keyChain.sign(data, self._certificateName)
        encodedData = data.wireEncode()

        dump("Sent content", content)
        transport.send(encodedData.toBuffer())

    def onRegisterFailed(self, prefix):
        self._responseCount += 1
        dump("Register failed for prefix", prefix.toUri())

def getSerial():
    try:
        with open('/proc/cpuinfo') as f:
            for line in f:
                if line.startswith('Serial'):
                    serial = line.split(':')[1].strip()
                    return serial
    except IOError:
        return 'nonononono'

def main():
    face = Face("localhost")

    # TODO: Change to my own storage
    identityStorage = MemoryIdentityStorage()
    privateKeyStorage = MemoryPrivateKeyStorage()
    keyChain = KeyChain(
      IdentityManager(identityStorage, privateKeyStorage), None)
    keyChain.setFace(face)

    # Initialize the storage.
    keyName = Name("/testname/DSK-123")
    certificateName = keyName.getSubName(0, keyName.size() - 1).append(
      "KEY").append(keyName[-1]).append("ID-CERT").append("0")
    identityStorage.addKey(keyName, KeyType.RSA, Blob(DEFAULT_PUBLIC_KEY_DER))
    privateKeyStorage.setKeyPairForKeyName(
      keyName, DEFAULT_PUBLIC_KEY_DER, DEFAULT_PRIVATE_KEY_DER)

    # serial = getSerial()
    # TODO: How do we factor in timestamp at end of prefix?
    echo = Echo(keyChain, certificateName)
    prefix = Name("/ndn/ucla.edu/pitest/data/") # TODO: /pitest/<serial>/data?
    dump("Register prefix", prefix.toUri())
    face.registerPrefix(prefix, echo.onInterest, echo.onRegisterFailed)

    while echo._responseCount < 1:
        face.processEvents()
        # We need to sleep for a few milliseconds so we don't use 100% of the CPU.
        time.sleep(0.01)    

    face.shutdown()

main()
