import time
from pyndn import Name
from pyndn import Face
from pyndn import Interest
from pyndn import Exclude

import json

response = False
timeout = False
exclude = Exclude()
face = Face("localhost")

def onData(interest, data):
    global response
    response = True
    print "Interest:", interest.getName().toUri(),
    print "Data:", data.getName().toUri(),
    print "Content:", data.getContent().toRawStr()
    print "Excluding:", data.getName().get(3).toEscapedString()
    exclude.appendComponent(data.getName().get(3))

def onTimeout(interest):
    global response
    response = True
    global timeout
    timeout = True
    print "Timeout:", interest.getName().toUri()

while not timeout:
    interest = Interest(Name("/home/pir/00000000d1f2533912"))
    interest.setExclude(exclude)
    print "Interest:", interest.getName().toUri()
    print "\tExcludes:", interest.getExclude().toUri()
    face.expressInterest(interest, onData, onTimeout)

    while not response:
        face.processEvents()
        time.sleep(0.5)
