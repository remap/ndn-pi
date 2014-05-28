import time
from pyndn import Name
from pyndn import Face
from pyndn import Interest
from pyndn import Exclude

import json
from threading import Thread, Event
import sys

class ExpressInterestThread(Thread):
    def __init__(self, consumer, event, face, statuses):
        Thread.__init__(self)
        self._consumer = consumer
        self._stopped = event
        self._face = face
        self._count = 0
        self._exclude = Exclude()
        self._statuses = statuses

    def onData(self, interest, data):
        print "Got data packet with name", data.getName().toUri(), "and content", data.getContent().toRawStr()
        pirSerial = data.getName().get(2)
        timestamp = data.getName().get(3)
        content = data.getContent().toRawStr()
        payload = json.loads(content)
        self._consumer.updateStatus(pirSerial.toEscapedString(), int(timestamp.toEscapedString()), payload["pir"])
#        if not self._exclude.matches(pirSerial):
#            self._exclude.appendComponent(pirSerial)
#        interest = Interest(Name("/home/pir"))
#        interest.setExclude(self._exclude)
#        print "Interest with exclude", interest.getExclude().toUri()
#        self._face.expressInterest(interest, self.onData, self.onTimeout)

    def onTimeout(self, interest):
        print "Time out for interest", interest.getName().toUri()

    def run(self):
        while not self._stopped.wait(2.25): # TODO: change to 0.25
            for dev in self._statuses.keys():
                # self._exclude.clear()
                interest = Interest(Name("/home/pir").append(dev))
                if len(self._statuses[dev]) > 0:
                    self._exclude.clear()
                    self._exclude.appendComponent(str(self._statuses[dev][-1][0]))
                    interest.setExclude(self._exclude)
                interest.setInterestLifetimeMilliseconds(1000.0)
                print "Send interest:", interest.getName().toUri(),
                print "exclude:", interest.getExclude().toUri()
                self._face.expressInterest(interest, self.onData, self.onTimeout)
                self._count += 1

class Discoverer(object):
    def __init__(self):
        self._timeout = False
        self._response = False
        self._exclude = Exclude()
        self._face = Face("localhost")
        self._statuses = { "00000000d1f2544912" : [] }

    def updateStatus(self, pir, time, value):
        self._statuses[pir].append((time, value))
        print "STATUSES:", self._statuses

    def run(self):

        # Start issuing interests to "/home/pir/" + self._devices[0]
        stopFlag = Event()
        thread = ExpressInterestThread(self, stopFlag, self._face, self._statuses)
        thread.start()

        try:
            while True:
                self._face.processEvents()
                time.sleep(0.01)
        except:
            stopFlag.set()
            raise

        self._face.shutdown()

if __name__ == "__main__":
    d = Discoverer()
    d.run()


