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
from pyndn.security import KeyChain

import subprocess
from os.path import expanduser, join

from sensors.pir import Pir

pir = Pir(12)

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
            pirVal = pir.read()
            content = time.strftime("%d %b, %Y %H:%M:%S") + str(pirVal)
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

    # Initialize the storage.
    keyChain = KeyChain()
    face.setCommandSigningInfo(keyChain, keyChain.getDefaultCertificateName())

    serial = getSerial()
    # TODO: How do we factor in timestamp at end of prefix?
    echo = Echo(keyChain, keyChain.getDefaultCertificateName())
    prefix = Name("/home/dev/" + serial + "/data")
    dump("Register prefix", prefix.toUri())
    face.registerPrefix(prefix, echo.onInterest, echo.onRegisterFailed)

    while echo._responseCount < 1:
        face.processEvents()
        # We need to sleep for a few milliseconds so we don't use 100% of the CPU.
        time.sleep(0.01)    

    face.shutdown()

main()
