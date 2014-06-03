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
        self._loop = asyncio.get_event_loop()
        self._face = ThreadsafeFace(self._loop, "localhost")
        self._pirStatuses = {}


    # Discovery
    def onDataDiscovery(self, interest, data):
        logging.info("Received data: " + data.getName().toUri())
        logging.info("\tContent: " + data.getContent().toRawStr())

        # TODO: save device for each Pir so I can remove pirs if no response
        payload = json.loads(data.getContent().toRawStr())
        for func in payload["functions"]:
            if func["type"] == "pir":
                pirId = func["id"]
                if pirId not in self._pirStatuses:
                    self._pirStatuses[pirId] = PirStatus(pirId)
            elif func["type"] == "cec":
                logging.info("CEC node, do nothing right now")

        # Reissue interest for "/home/dev" excluding devId just received
        devId = data.getName().get(2)
        interest.getExclude().appendComponent(devId)
        self.expressDiscoveryInterest(interest)

        # Print discovery statuses
        logging.info("STATUSES: " + str(self._pirStatuses))

    def onTimeoutDiscovery(self, interest):
        logging.info("Timeout interest: " + interest.getName().toUri())
        logging.info("Device and resource discovery complete, rescheduling again in 600 seconds")
        self._loop.call_later(600, self.initDiscovery)

    def expressDiscoveryInterest(self, interest):
        self._face.expressInterest(interest, self.onDataDiscovery, self.onTimeoutDiscovery)
        logging.info("Sent interest: " + interest.getName().toUri())
        logging.info("\tExclude: " + interest.getExclude().toUri())
        logging.info("\tLifetime: " + str(interest.getInterestLifetimeMilliseconds()))

    def initDiscovery(self):
        logging.info("Beginning device and resource discovery")
        interest = Interest(Name("/home/dev"))
        interest.setInterestLifetimeMilliseconds(4000.0)
        interest.setMinSuffixComponents(2)
        interest.setMaxSuffixComponents(2)
        # includes implicit digest so to match "/home/dev/<dev-id>" must have 2 components

        # Express initial discovery interest
        self.expressDiscoveryInterest(interest)


    # Pir Consumption
    def onDataPir(self, interest, data):
        self._callbackCountData += 1
        logging.info("Got data: " + data.getName().toUri())
        logging.info("\tContent: " + data.getContent().toRawStr())

        # Extract info from data packet
        payload = json.loads(data.getContent().toRawStr())
        pirId = data.getName().get(2).toEscapedString()
        timeComponent = data.getName().get(3)
        timestamp = int(timeComponent.toEscapedString())
        pirVal = payload["pir"]

        # Update pirStatus information: add data, exclude last received timestamp
        self._pirStatuses[pirId].setExcludeUpTo(timeComponent)
        if self._pirStatuses[pirId].addData(timestamp, pirVal):
            self._callbackCountUniqueData += 1

        logging.info("STATUSES: " + str(self._pirStatuses)) # TODO: Cleanup
        self.controlTV()

    def onTimeoutPir(self, interest):
        self._callbackCountTimeout += 1
        logging.info("Timeout interest: " + interest.getName().toUri())

    def expressInterestPirAndRepeat(self):
        logging.info("callbackCountUniqueData: " + str(self._callbackCountUniqueData) + "callbackCountTimeout: " + str(self._callbackCountTimeout))

        # Express interest for each pir we have discovered
        for pirId, pirStatus in self._pirStatuses.iteritems():
            interest = Interest(Name("/home/pir").append(pirId))
            interest.setExclude(pirStatus.getExclude())
            interest.setInterestLifetimeMilliseconds(1000.0)
            interest.setChildSelector(1)

            self._face.expressInterest(interest, self.onDataPir, self.onTimeoutPir)
            self._countExpressedInterests += 1
            logging.info("Sent interest: " + interest.getName().toUri())
            logging.info("\tExclude: " + interest.getExclude().toUri())
            logging.info("\tLifetime: " + str(interest.getInterestLifetimeMilliseconds()))
 
        # Reschedule again in 0.5 sec
        self._loop.call_later(0.5, self.expressInterestPirAndRepeat)

    def controlTV(self):
        count = 0
        for pirId, pirStatus in self._pirStatuses.iteritems():
            if pirStatus.getLatestValue():
                count += 1
        if count >= 2:
            # TODO: Send command interest to TV
            pass
        

    # Set up all async function calls
    def run(self):
        self._face.stopWhen(lambda: self._callbackCountUniqueData >= 20)
        self._loop.call_soon(self.initDiscovery)
        self._loop.call_soon(self.expressInterestPirAndRepeat)
        self._loop.run_forever() # Run until stopWhen stops the loop
        self._face.shutdown()

if __name__ == "__main__":
    c = Consumer()
    c.run()
