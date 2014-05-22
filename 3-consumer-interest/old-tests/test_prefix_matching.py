import time
from pyndn import Name
from pyndn import Interest
from pyndn import Face
from pyndn.security import KeyChain

def onInterest(prefix, interest, transport, registeredPrefixId):
    print "Got interest for", interest.getName().toUri(), "at prefix", prefix.toUri()

def onRegisterFailed(prefix):
    print "Register failed for prefix", prefix.toUri()

face = Face("localhost")
keyChain = KeyChain()
face.setCommandSigningInfo(keyChain, keyChain.getDefaultCertificateName())

face.registerPrefix(Name("/home/1"), onInterest, onRegisterFailed)
face.registerPrefix(Name("/home/2"), onInterest, onRegisterFailed)
face.registerPrefix(Name("/home/3"), onInterest, onRegisterFailed)
face.registerPrefix(Name("/home/4"), onInterest, onRegisterFailed)
face.registerPrefix(Name("/home/5"), onInterest, onRegisterFailed)

while True:
    face.processEvents()
    time.sleep(0.01)    
