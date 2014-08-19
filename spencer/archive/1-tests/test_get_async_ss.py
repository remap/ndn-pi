# -*- Mode:python; c-file-style:"gnu"; indent-tabs-mode:nil -*- */
#
# Copyright (C) 2014 Regents of the University of California.
# Author: Jeff Thompson <jefft0@remap.ucla.edu>
# See COPYING for copyright and distribution information.
#

import time
from pyndn import Name
from pyndn import Face

def dump(*list):
    result = ""
    for element in list:
        result += (element if type(element) is str else repr(element)) + " "
    print(result)

class Counter(object):
    def __init__(self):
        self._callbackCount = 0

    def onData(self, interest, data):
        self._callbackCount += 1
        dump("Got data packet with name", data.getName().toUri())
        # Use join to convert each byte to chr.
        dump(data.getContent().toRawStr())

    def onTimeout(self, interest):
        self._callbackCount += 1
        dump("Time out for interest", interest.getName().toUri()) 

def main():
    face = Face("localhost")
    
    counter = Counter()

    name0 = Name("/home")
    dump("Express name ", name0.toUri())
    face.expressInterest(name0, counter.onData, counter.onTimeout)

    name1 = Name("/home/dev/00000000d1f25339/data/temp")
    dump("Express name ", name1.toUri())
    face.expressInterest(name1, counter.onData, counter.onTimeout)

    name2 = Name("/home/dev/00000000d1f25339/data/pir")
    dump("Express name ", name2.toUri())
    face.expressInterest(name2, counter.onData, counter.onTimeout)

    while counter._callbackCount < 3:
        face.processEvents()
        # We need to sleep for a few milliseconds so we don't use 100% of the CPU.
        time.sleep(0.01)    

    face.shutdown()

main()
