# Copyright (C) 2014 Regents of the University of California.
# Author: Spencer Sutterlin <ssutterlin1@ucla.edu>
# 
# This file is part of ndn-pi (Named Data Networking - Pi).
#
# ndn-pi is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
# A copy of the GNU General Public License is in the file COPYING.

import time
from pyndn import Name
from pyndn import Interest
from pyndn import Data
from pyndn import Face
from pyndn.security import KeyChain

import subprocess
from os.path import expanduser, join
import socket
from sensors.pir import Pir
import struct
import json

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
        self.pir = Pir(12)
        
        self._keyChain = KeyChain()
        self._certificateName = self._keyChain.getDefaultCertificateName() # Might need to change
        # # OLD stuff from loadKey()
        # self.key = pyccn.Key()
        # self.key.fromPEM(filename = keyFile)
        # self.key_name = pyccn.Name("/ndn/ucla.edu/bms/strathmore/data").appendKeyID(self.key)
        # print 'Use key name ' + str(self.key_name) + ' to sign data'
        # self.si = pyccn.SignedInfo(self.key.publicKeyID, pyccn.KeyLocator(self.key_name))

    def publishData(self, payload, timestamp):
        #timestampPacked = struct.pack('!Q', timestamp)
        dataName = Name(self.prefix).append(str(timestamp))
        #dataName = Name(self.prefix).append(timestampPacked)
        data = Data(dataName)

        content = json.dumps(payload)
        data.setContent(content)

        # how to set co.signedInfo?
        # co.signedInfo = self.si # OLD

        # TODO: Make sure signing worked right
        self._keyChain.sign(data, self._certificateName)
        print "Published Data:", data.getName().toUri(), "with content:", content, "to repo"
        self.publisher.put(data)

    def expressCommandInterestDataSetReady(self, timestamp):
        interest = Interest(Name("/home/all/command/datasetready").append(self.prefix).append(str(timestamp)))
        interest.setInterestLifetimeMilliseconds(3000)
        # TODO: Start timer
        self.commandInterestFace.expressInterest(interest, self.onData, self.onTimeout)
        print "Sent Command Interest:", interest.getName().toUri()
        # TODO: probably shouldn't directly call self.expressCommandInterestDataSetReady on timeout (= infinite loop if fail)

    def onTimeout(self, interest):
        print "Interest:", interest.getName().toUri(), "timed out"
        # call expressInterest again

    def onData(self, interest, data):
        # TODO: how to tweak the onData function to receive interests
        # Whoop-de-friggin-do
        print "Received Data:", data.getName().toUri(), "with content:", data.getContent().toRawStr()

    def run(self):
        # Publish first packet regardless of change
        prevPirVal = pirVal = self.pir.read()
        payload = {'pir':pirVal}
        timestamp = int(time.time() * 1000) # in milliseconds
        self.publishData(payload, timestamp)
        sample_count = 1

        # Wait 0.5 sec for data to be inserted into repo
        time.sleep(0.5)

        #timestampPacked = struct.pack('!Q', timestamp)
        #self.expressCommandInterestDataSetReady("/dev/" + self.serial + "/pir/0/data/" + timestampPacked)
        self.expressCommandInterestDataSetReady(timestamp)

        while (True):
            pirVal = self.pir.read()
            if prevPirVal != pirVal:
                payload = {'pir':pirVal}
                timestamp = int(time.time() * 1000) # in milliseconds
                #timestampPacked = struct.pack('!Q', timestamp)
                self.publishData(payload, timestamp)
                sample_count += 1

                # Wait 0.5 sec for data to be inserted into repo
                time.sleep(0.5)

                # TODO: Express command interest
                #self.expressCommandInterestDataSetReady("/dev/" + self.serial + "/pir/0/data/" + timestampPacked)
                self.expressCommandInterestDataSetReady(timestamp)

                prevPirVal = pirVal

            self.commandInterestFace.processEvents()
            time.sleep(self.interval)

if __name__ == "__main__":
    logger = PirDataLogger(data_interval = 0.5) # sample at every 0.5 seconds (also affects face.processEvents)
    logger.run()