import asyncio
from pyndn import Name
from pyndn import Interest
from pyndn import ThreadsafeFace

import logging
logging.basicConfig(filename="async.log", level=logging.INFO)


class Counter(object): # ResponseHandler
    def __init__(self):
        self._callbackCount = 0
        self._stopped = False

    def onData(self, interest, data):
        self._callbackCount += 1
        logging.info("Data: " + data.getName().toUri())
        logging.info("Content: " + data.getContent().toRawStr())

    def onTimeout(self, interest):
        self._callbackCount += 1
        logging.info("Timeout interest: " + interest.getName().toUri())

class Consumer(object):
    def __init__(self):
        self._loop = asyncio.get_event_loop()
        self._face = ThreadsafeFace(self._loop, "localhost")
        self._counter = Counter()
        self._pirStatuses = {}

    def express_interest_and_repeat(self, loop):
        logging.info("Counter's callbackCount: " + str(self._counter._callbackCount))
        # Express interest here
        interest = Interest(Name("/home/pir/00000000d1f2533912"))
        # interest.setExclude(exclude)
        interest.setInterestLifetimeMilliseconds(2000.0)
        logging.info("Send interest: " + interest.getName().toUri())
        # print "exclude:", interest.getExclude().toUri()
        self._face.expressInterest(interest, self._counter.onData, self._counter.onTimeout)
        loop.call_later(0.25, self.express_interest_and_repeat, loop) # there is call_soon_threadsafe but no call_later_threadsafe
        

    def run(self):
        self._face.stopWhen(lambda: self._counter._callbackCount >= 10)
        self._loop.call_soon(self.express_interest_and_repeat, self._loop) # might need _threadsafe
        # Run until stopWhen stops the loop.
        self._loop.run_forever()
        self._face.shutdown()

if __name__ == "__main__":
    c = Consumer()
    c.run()
