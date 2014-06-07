from pyndn import Name
from pyndn import Interest
from pyndn import Exclude
from pyndn import ThreadsafeFace
from pyndn.security import KeyChain
from app.remote_device import RemoteDevice
try:
    import asyncio
except ImportError:
    import trollius as asyncio
import json
import logging
logging.basicConfig(level=logging.INFO)

class Consumer(object):
    def __init__(self):
        self._countExpressedInterests = 0
        self._callbackCountData = 0
        self._callbackCountUniqueData = 0
        self._callbackCountTimeout = 0

        self._loop = asyncio.get_event_loop()
        self._face = ThreadsafeFace(self._loop, "localhost")
        self._keyChain = KeyChain()
        self._certificateName = self._keyChain.getDefaultCertificateName()
        self._face.setCommandSigningInfo(self._keyChain, self._certificateName)

        self._remoteDevices = []

        # TODO: NFD hack: remove once NFD forwarding fixed
        self._oneTimeoutAlready = False

    # Discovery
    def onDataDiscovery(self, interest, data):
        logging.debug("Received data: " + data.getName().toUri())
        logging.debug("\tContent: " + data.getContent().toRawStr())

        # TODO: save device for each Pir so I can remove pirs if no response
        payload = json.loads(data.getContent().toRawStr())
        for func in payload["functions"]:
            type = func["type"]
            id = func["id"]
            if not any(x.type == type and x.id == id for x in self._remoteDevices):
                logging.info("New device discovered: " + type + " " + id)
                self._remoteDevices.append(RemoteDevice(type, id))

        # Reissue interest for "/home/dev" excluding devId just received
        devId = data.getName().get(2)
        interest.getExclude().appendComponent(devId)
        self.expressDiscoveryInterest(interest)
        logging.info("Reissue discovery interest for \"/home/dev/\", excluding already discovered devices")

    def onTimeoutDiscovery(self, interest):
        logging.debug("Timeout interest: " + interest.getName().toUri())
        logging.info("Discovery complete, rescheduling again in 600 seconds")
        logging.info("Devices discovered: " + str(self._remoteDevices))

        # TODO: NFD hack: uncomment once NFD forwarding fixed
        # self._loop.call_later(600, self.initDiscovery)

        # TODO: NFD hack: remove once NFD forwarding fixed
        if self._oneTimeoutAlready:
            self._oneTimeoutAlready = False
            self._loop.call_later(600, self.initDiscovery)
        else:
            self._oneTimeoutAlready = True

    def expressDiscoveryInterest(self, interest):
        self._face.expressInterest(interest, self.onDataDiscovery, self.onTimeoutDiscovery)
        logging.debug("Sent interest: " + interest.getName().toUri())
        logging.debug("\tExclude: " + interest.getExclude().toUri())
        logging.debug("\tLifetime: " + str(interest.getInterestLifetimeMilliseconds()))

    def initDiscovery(self):
        logging.info("Begin discovery, issue discovery interest for \"/home/dev\"")
        interest = Interest(Name("/home/dev"))
        interest.setInterestLifetimeMilliseconds(4000.0)
        interest.setMinSuffixComponents(2)
        interest.setMaxSuffixComponents(2)
        # includes implicit digest so to match "/home/dev/<dev-id>" must have 2 components

        # Express initial discovery interest
        self.expressDiscoveryInterest(interest)

        # TODO: NFD hack: remove once NFD forwarding fixed
        interest = Interest(Name("/home/localdev"))
        interest.setInterestLifetimeMilliseconds(4000.0)
        interest.setMinSuffixComponents(2)
        interest.setMaxSuffixComponents(2)
        self.expressDiscoveryInterest(interest)


    # Pir Consumption
    def onDataPir(self, interest, data):
        self._callbackCountData += 1
        logging.debug("Got data: " + data.getName().toUri())
        logging.debug("\tContent: " + data.getContent().toRawStr())

        # Extract info from data packet
        payload = json.loads(data.getContent().toRawStr())
        pirId = data.getName().get(2).toEscapedString()
        timeComponent = data.getName().get(3)
        timestamp = int(timeComponent.toEscapedString())
        pirVal = payload["pir"]

        # Update pirStatus information: add data, exclude last received timestamp
        pir = next((x for x in self._remoteDevices if x.type == "pir" and x.id == pirId), None)
        pir.status.setExcludeUpTo(timeComponent)
        if pir.status.addData(timestamp, pirVal):
            self._callbackCountUniqueData += 1

        logging.info("pir " + str(pirId) + " " + str(pirVal) + " at " + str(timestamp))
        self.controlTV()

    def onTimeoutPir(self, interest):
        self._callbackCountTimeout += 1
        logging.debug("Timeout interest: " + interest.getName().toUri())

    def expressInterestPirAndRepeat(self):
        logging.debug("callbackCountUniqueData: " + str(self._callbackCountUniqueData) + ", callbackCountTimeout: " + str(self._callbackCountTimeout))

        # Express interest for each pir we have discovered
        pirs = [ x for x in self._remoteDevices if x.type == "pir" ]
        for pir in pirs:
            interest = Interest(Name("/home/pir").append(pir.id))
            interest.setExclude(pir.status.getExclude())
            interest.setInterestLifetimeMilliseconds(1000.0)
            interest.setChildSelector(1)

            self._face.expressInterest(interest, self.onDataPir, self.onTimeoutPir)
            self._countExpressedInterests += 1
            logging.debug("Sent interest: " + interest.getName().toUri())
            logging.debug("\tExclude: " + interest.getExclude().toUri())
            logging.debug("\tLifetime: " + str(interest.getInterestLifetimeMilliseconds()))
 
        # Reschedule again in 0.5 sec
        self._loop.call_later(0.5, self.expressInterestPirAndRepeat)


    # Cec Control
    def onDataCec(self, interest, data):
        print "onDataCec"

    def onTimeoutCec(self, interest):
        print "onTimeoutCec"

    def controlTV(self):
        count = 0
        pirs = [ x for x in self._remoteDevices if x.type == "pir" ]
        cecs = [ x for x in self._remoteDevices if x.type == "cec" ]
        for pir in pirs:
            if pir.status.getLastValue():
                count += 1
        if count >= 2:
            # TODO: Send command interest to TV
            logging.info("STATUSES: " + str(self._remoteDevices)) # TODO: Cleanup
            logging.info("turn on tv")
            for cec in cecs:
                # TODO: change .append("play") to be TLV
                interest = Interest(Name("/home/cec").append(cec.id).append("play"))
                # self._face.makeCommandInterest(interest)
                self._face.expressInterest(interest, self.onDataCec, self.onTimeoutCec)
        

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
