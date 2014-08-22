from __future__ import print_function
from ndn_pi.iot_node import IotNode
from pyndn import Name, Data, Interest
import json
from sys import stdin, stdout
try:
    import asyncio
except ImportError:
    import trollius as asyncio
    from trollius import Return, From

class ViewerNode(IotNode):
    def __init__(self, filename=None):
        if filename is None:
            filename = 'viewer.conf'
        super(ViewerNode, self).__init__(filename)
        self._networkListing = {}
        self._lastPresentedList = []

    def setupComplete(self):
        self._loop.call_soon(self.getDeviceList)
        self._loop.call_soon(self.displayMenu)
        self._loop.add_reader(stdin, self.handleUserInput)

    def onTimeout(self, interest):
        #try again
        self.log.warn('Timeout on device list')
        self._loop.call_later(5, self.getDeviceList)

    def onReceivedList(self, interest, data):
        #print ("Received:\n{}".format(data.getContent().toRawStr()))
        self._networkListing = json.loads(data.getContent().toRawStr())
        self._loop.call_later(30, self.getDeviceList)

    def displayMenu(self):
        menuStr = ''
        try:
            # keep old state in case the device list updates while the user is thinking
            self._lastPresentedList = self._networkListing["light"]
        except KeyError:
            self._lastPresentedList = []
        else:
            i = 1
            for info in self._lastPresentedList:
                signInfo = "signed" if info["signed"] else "unsigned"
                menuStr += '\t{}: {} ({})\n'.format(i, info["name"], signInfo)
                i += 1
            menuStr += 'Enter "on <n>" or "off <n>" to turn a light on or off\n'
        menuStr += 'Enter "quit" to quit, anything else to refresh device list.'

        print(menuStr)
        print ("> ", end="")
        stdout.flush()


    def interestTimedOut(self, interest):
        self.log.warn("Timed out on light command")
        self._loop.call_soon(self.displayMenu)

    def lightAckReceived(self, interest, data):
        self.log.info("Received ack from lights")
        self._loop.call_soon(self.displayMenu)


    def handleUserInput(self):
        inputStr = stdin.readline()

        if inputStr.upper().startswith('Q'):
            self._isStopped = True
        else:
            inputCommand = inputStr.strip().split()
            try:
                commandType = inputCommand[0]
                chosenIdx = int(inputCommand[1]) - 1
                if commandType == 'off' or commandType == 'on' and chosenIdx >= 0:
                    chosenDevice = self._lastPresentedList[chosenIdx]
                    chosenName = chosenDevice["name"]

                    commandInterest = Interest(Name(chosenName).append(commandType))
                    commandInterest.setInterestLifetimeMilliseconds(5000)
                    if chosenDevice["signed"]:
                        self._face.makeCommandInterest(commandInterest)
                    self._face.expressInterest(commandInterest, self.lightAckReceived, self.interestTimedOut)
                else:
                    self._loop.call_soon(self.displayMenu)
            except IndexError, KeyError:
                self._loop.call_soon(self.displayMenu)
        

    def getDeviceList(self):
        interestName = Name(self._policyManager.getTrustRootIdentity()).append('listDevices')
        self._face.expressInterest(interestName, self.onReceivedList, self.onTimeout)

if __name__ == '__main__':
    node = ViewerNode()
    node.start()

"""
        self._stdinSelector = selectors.DefaultSelector()
        self._stdinSelector.register(stdin, selectors.EVENT_READ, self.handleUserInput)

    def setupComplete(self):
        self._loop.call_soon(self.getDeviceList)
        self._loop.call_soon(self.displayMenu)

    def onTimeout(self, interest):
        #try again
        self.log.warn('Timeout on device list')
        self._loop.call_later(5, self.getDeviceList)

    def onReceivedList(self, interest, data):
        print ("Received:\n{}".format(data.getContent().toRawStr()))
        self._loop.call_later(30, self.getDeviceList)

    def displayMenu(self):
        print (self._networkListing)
        print (">", end="", flush=True)

        events = self._stdinSelector.select()
        for (key, _) in events:
            callback = key.data
            inputStr = key.fileobj.readline()
            callback(inputStr)
"""
