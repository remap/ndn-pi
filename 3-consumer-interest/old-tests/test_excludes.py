import time
from pyndn import Name
from pyndn import Face
from pyndn import Interest
from pyndn import Exclude

import json

callbacks = 0
exclude = Exclude()

def onData(interest, data):
    global callbacks
    callbacks += 1
    print "Interest:", interest.getName().toUri(), "data:", data.getName().toUri(), "content:", data.getContent().toRawStr()
    print data.getName().get(len(data.getName())-1).toEscapedString()
    exclude.appendComponent(data.getName().get(len(data.getName())-1).toEscapedString())
#    exclude.appendComponent(data.getName().getSubName(len(data.getName())-1).toUri())

def onTimeout(interest):
    global callbacks
    callbacks += 1
    print "Timeout:", interest.getName().toUri()

face = Face("localhost")
interest = Interest(Name("/home/pir"))
print "Interest:", interest.getName().toUri()
print "\tExcludes:", interest.getExclude().toUri()
face.expressInterest(interest, onData, onTimeout)

while callbacks < 1:
    face.processEvents()
    time.sleep(0.01)

interest = Interest(Name("/home/pir"))
interest.setExclude(exclude)
print "Interest:", interest.getName().toUri()
print "\tExcludes:", interest.getExclude().toUri()
face.expressInterest(interest, onData, onTimeout)

while callbacks < 2:
    face.processEvents()
    time.sleep(0.01)

interest = Interest(Name("/home/pir"))
interest.setExclude(exclude)
print "Interest:", interest.getName().toUri()
print "\tExcludes:", interest.getExclude().toUri()
face.expressInterest(interest, onData, onTimeout)

while callbacks < 3:
    face.processEvents()
    time.sleep(0.01)
