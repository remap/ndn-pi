import asyncio
from pyndn import Name
from pyndn import Interest
from pyndn import Exclude
from pyndn import ThreadsafeFace

import time
import json
from app.pir_status import PirStatus
import logging
logging.basicConfig(filename="async.log", level=logging.INFO)

class Consumer(object):
    def __init__(self):
        self._countExpressedInterests = 0
        self._callbackCountData = 0
        self._callbackCountUniqueData = 0
        self._callbackCountTimeout = 0
        self._discoveryTimeout = False
        self._response = False
        self._stopped = False
        self._loop = asyncio.get_event_loop()
        self._face = ThreadsafeFace(self._loop, "localhost")
        self._exclude = Exclude()
        self._deviceExclude = Exclude()
        self._pirStatuses = {} # { "00000000d1f2533912" : {} }

    def onDataDev(self, interest, data):
#        self._response = True
        logging.info("Data: " + data.getName().toUri())
        logging.info("Content: " + data.getContent().toRawStr())
        payload = json.loads(data.getContent().toRawStr())
        for func in payload["functions"]:
            if func["type"] == "pir":
                pirId = func["id"]
                self._pirStatuses[pirId] = PirStatus(pirId)
#                self._pirStatuses[func["id"]] = {}
            elif func["type"] == "cec":
                logging.info("CEC node, do nothing right now")
#        self._deviceExclude.appendComponent(data.getName().get(2))
        devId = data.getName().get(2)
        interest.getExclude().appendComponent(devId)
        for k, v in self._pirStatuses.iteritems():
            logging.info("STATUSES: " + str(v))
#        logging.info("STATUSES: " + str(self._pirStatuses))
#        self.expressDiscoveryInterest()
        self.expressDiscoveryInterest(interest)

    def onDataPir(self, interest, data):
        self._callbackCountData += 1
        logging.info("Data: " + data.getName().toUri())
        logging.info("Content: " + data.getContent().toRawStr())
        pirId = data.getName().get(2).toEscapedString()
        timeComponent = data.getName().get(3)
        self._pirStatuses[pirId].excludeUpTo(timeComponent)

        # TODO: modify, save status
        payload = json.loads(data.getContent().toRawStr())
        pirVal = payload["pir"]
        timestamp = int(timeComponent.toEscapedString())
        if self._pirStatuses[pirId].addData(timestamp, pirVal):
            self._callbackCountUniqueData += 1
        logging.info("STATUSES: " + str(self._pirStatuses))

    def onTimeout(self, interest):
        self._callbackCountTimeout += 1
        logging.info("Timeout interest: " + interest.getName().toUri())

    def onDiscoveryTimeout(self, interest):
        self._discoveryTimeout = True
        logging.info("Timeout interest: " + interest.getName().toUri())

    def express_interest_and_repeat(self, loop):
        logging.info("callbackCountUniqueData: " + str(self._callbackCountUniqueData) + "callbackCountTimeout: " + str(self._callbackCountTimeout))
        # Express interest here
        for pirId, pirStatus in self._pirStatuses.iteritems():
            interest = Interest(Name("/home/pir").append(pirId))
            interest.setExclude(pirStatus.getExclude())
            interest.setInterestLifetimeMilliseconds(1000.0)
            interest.setChildSelector(1)
            logging.info("Send interest: " + interest.getName().toUri())
            logging.info("Exclude: " + interest.getExclude().toUri())
            self._face.expressInterest(interest, self.onDataPir, self.onTimeout)
            self._countExpressedInterests += 1
        loop.call_later(0.5, self.express_interest_and_repeat, loop)

    def expressDiscoveryInterest(self, interest):
        logging.info("Send interest: " + interest.getName().toUri())
        logging.info("Exclude: " + interest.getExclude().toUri())
        self._face.expressInterest(interest, self.onDataDev, self.onDiscoveryTimeout)

    def discovery(self, loop):
        interest = Interest(Name("/home/dev"))
        interest.setInterestLifetimeMilliseconds(4000.0)
        self.expressDiscoveryInterest(interest)
        loop.call_later(600, self.discovery, loop)

    def run(self):
        self._loop.call_soon(self.discovery, self._loop)
        # self._face.stopWhen(lambda: self._timeout or self._response)
        # self._loop.run_forever()

        self._face.stopWhen(lambda: self._callbackCountUniqueData >= 5)
        self._loop.call_soon(self.express_interest_and_repeat, self._loop)
        # Run until stopWhen stops the loop.
        self._loop.run_forever()
        self._face.shutdown()

if __name__ == "__main__":
    c = Consumer()
    c.run()
