import time
from pyndn import Name
from pyndn import Data
from pyndn import Face
from pyndn.security import KeyChain

import subprocess
from os.path import expanduser, join
import socket
from sensors.pir import Pir
import struct

def getSerial():
    with open('/proc/cpuinfo') as f:
        for line in f:
            if line.startswith('Serial'):
                return line.split(':')[1].strip()

class RepoSocketPublisher:
    def __init__(self, repo_port):
        self.repo_dest = ('::1', int(repo_port))

        self.sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        self.sock.connect(self.repo_dest)

    def put(self, data):
        encodedData = data.wireEncode()
        self.sock.sendall(str(bytearray(encodedData.toBuffer())))

class PirDataLogger:
    def __init__(self, data_interval):
        # connect to local repo
        self.publisher = RepoSocketPublisher(12345)
        self.serial = getSerial()
        self.prefix = Name("/home/dev/" + self.serial + "/pir/0/data")
        self.commandInterestFace = Face("localhost")
        self.interval = data_interval
        self.pir = Pir()
        
        self._keyChain = KeyChain()
        self._certificateName = self._keyChain.getDefaultCertificateName() # Might need to change
        # # OLD stuff from loadKey()
        # self.key = pyccn.Key()
        # self.key.fromPEM(filename = keyFile)
        # self.key_name = pyccn.Name("/ndn/ucla.edu/bms/strathmore/data").appendKeyID(self.key)
        # print 'Use key name ' + str(self.key_name) + ' to sign data'
        # self.si = pyccn.SignedInfo(self.key.publicKeyID, pyccn.KeyLocator(self.key_name))

    def publishData(self, payload, timestamp):
        timestampPacked = struct.pack('!Q', timestamp)
        data = Data(self.prefix.append(timestampPacked))

        content = json.dumps(payload)
        data.setContent(content)
        # co.content = json.dumps(payload) # OLD

        # how to set co.signedInfo?
        # co.signedInfo = self.si # OLD

        self._keyChain.sign(data, self._certificateName)
        self.publisher.put(data)
        dump("Published data", content)
        dump("at ", timestamp_ms_packed)
        dump("named ", self.prefix.append(timestamp_ms_packed))
        print self.prefix # TODO: make sure self.prefix is "/home/dev/<serial>/pir/0/data"

    def expressDataReadyCommandInterest(self, name):
        interest = Interest(Name("/home/all/command/dataready/dataready/dev/" + self.serial + "/pir/0/data/"))
        interest.setInterestLifetimeMilliseconds(3000)
        # TODO: Start timer
        self.commandInterestFace.expressInterest(interest, counter.onData, expressDataReadyCommandInterest(name))
        # TODO: probably shouldn't directly call expressDataReadyCommandInterest on timeout (= infinite loop if fail)

    def onData(self, interest, data):
        # TODO: how to tweak the onData function to receive interests
        # Whoop-de-friggin-do
        pass

    def run(self):
        # Publish first packet regardless of change
        prevPirVal = pirVal = self.pir.read()
        payload = {'pir':pirVal}
        timestamp = int(time.time() * 1000) # in milliseconds
        self.publishData(payload, timestamp)
        sample_count = 1
        timestampPacked = struct.pack('!Q', timestamp)
        expressDataReadyCommandInterest("/dev/" + self.serial + "/pir/0/data/" + timestampPacked)

        while (True):
            pirVal = self.pir.read()
            if prevPirVal != pirVal:
                payload = {'pir':pirVal}
                timestamp = int(time.time() * 1000) # in milliseconds
                self.publishData(payload)
                sample_count += 1
                
                # TODO: Express command interest
                expressDataReadyCommandInterest("/dev/" + self.serial + "/pir/0/data/" + timestampPacked)
            
            time.sleep(self.interval)

if __name__ == "__main__":
    logger = PirDataLogger(data_interval = 0.5) # sample at every 0.5 seconds
    logger.run()
