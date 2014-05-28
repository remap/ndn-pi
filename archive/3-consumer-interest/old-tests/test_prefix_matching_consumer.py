import time
from pyndn import Name
from pyndn import Face

def onData(self, interest, data):
    print "onData"

def onTimeout(self, interest):
    print "onTimeout"

def main():
    face = Face("localhost")
    
    name0 = Name("/home")
    face.expressInterest(name0, onData, onTimeout)

    name1 = Name("/home/dev/cereal/")
    face.expressInterest(name1, onData, onTimeout)

    name2 = Name("/home/dev/cereal")
    face.expressInterest(name2, onData, onTimeout)

    name3 = Name("/home/dev/cereal/key")
    face.expressInterest(name3, onData, onTimeout)

    name4 = Name("/home/dev/cereal/0")
    face.expressInterest(name4, onData, onTimeout)

    name5 = Name("/home/dev/cereal/key/9")
    face.expressInterest(name5, onData, onTimeout)

    while True:
        face.processEvents()
        # We need to sleep for a few milliseconds so we don't use 100% of the CPU.
        time.sleep(0.01)    

    face.shutdown()

main()
