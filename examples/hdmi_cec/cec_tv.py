#!/usr/bin/python
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

from pyndn import Name, Data
from pyndn.encoding import ProtobufTlv
from util.common import Common
from ndn_pi.iot_node import IotNode
from app.cec import CecDevice, CecCommand
import app.cec_messages_pb2 as pb
import subprocess
import time

class CecTv(IotNode):
    def __init__(self):
        super(CecTv, self).__init__()
        self.addCommand(Name('sendCommand'), self.onCecCommand, ['cec'], True)
        
    def processCommands(self, message):
        PI = CecDevice.RECORDING_1
        # TODO: FORK SEPARATE THREAD FOR THIS
        self.log.debug("processCommands: "+ str(message.commands))
        if message.destination == pb.TV:
            processedDestination = CecDevice.TV
        elif message.destination == pb.RECORDING_1:
            processedDestination = CecDevice.RECORDING_1
        elif message.destination == pb.PLAYBACK_1:
            processedDestination = CecDevice.PLAYBACK_1
        elif message.destination == pb.RESERVED_E:
            processedDestination = CecDevice.RESERVED_E
        elif message.destination == pb.BROADCAST:
            processedDestination = CecDevice.BROADCAST
        else:
            raise RuntimeError("CecDevice/Message not enumerated/implemented")
        for command in message.commands:
            # TODO: Separate out cec-client call into init (remove -s flag for not single mode anymore)
            if command == pb.STANDBY:
                cecClient = subprocess.Popen(["cec-client", "-s", "-d", "1"], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
                processedCommand = "standby " + format(processedDestination, '01x')
                (out, err) = cecClient.communicate(input=processedCommand)
            elif command == pb.ON:
                cecClient = subprocess.Popen(["cec-client", "-s", "-d", "1"], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
                processedCommand = "on " + format(processedDestination, '01x')
                (out, err) = cecClient.communicate(input=processedCommand)
            elif command == pb.PLAY:
                #processedCommand = CecCommand.PLAY
                subprocess.check_call(["omxplayer", "-o", "hdmi", "small.mp4"])
            elif command == pb.PAUSE:
                cecClient = subprocess.Popen(["cec-client", "-s", "-d", "1"], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
                processedCommand = "tx " + format(PI, '01x') + format(processedDestination, '01x') + ":" + CecCommand.PAUSE
                (out, err) = cecClient.communicate(input=processedCommand)
            elif command == pb.FF:
                cecClient = subprocess.Popen(["cec-client", "-s", "-d", "1"], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
                processedCommand = "tx " + format(PI, '01x') + format(processedDestination, '01x') + ":" + CecCommand.FF
                (out, err) = cecClient.communicate(input=processedCommand)
            elif command == pb.RW:
                cecClient = subprocess.Popen(["cec-client", "-s", "-d", "1"], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
                processedCommand = "tx " + format(PI, '01x') + format(processedDestination, '01x') + ":" + CecCommand.RW
                (out, err) = cecClient.communicate(input=processedCommand)
            elif command == pb.SEL:
                cecClient = subprocess.Popen(["cec-client", "-s", "-d", "1"], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
                processedCommand = "tx " + format(PI, '01x') + format(processedDestination, '01x') + ":" + CecCommand.SEL
                (out, err) = cecClient.communicate(input=processedCommand)
            elif command == pb.UP:
                cecClient = subprocess.Popen(["cec-client", "-s", "-d", "1"], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
                processedCommand = "tx " + format(PI, '01x') + format(processedDestination, '01x') + ":" + CecCommand.UP
                (out, err) = cecClient.communicate(input=processedCommand)
            elif command == pb.DOWN:
                cecClient = subprocess.Popen(["cec-client", "-s", "-d", "1"], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
                processedCommand = "tx " + format(PI, '01x') + format(processedDestination, '01x') + ":" + CecCommand.DOWN
                (out, err) = cecClient.communicate(input=processedCommand)
            elif command == pb.LEFT:
                cecClient = subprocess.Popen(["cec-client", "-s", "-d", "1"], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
                processedCommand = "tx " + format(PI, '01x') + format(processedDestination, '01x') + ":" + CecCommand.LEFT
                (out, err) = cecClient.communicate(input=processedCommand)
            elif command == pb.RIGHT:
                cecClient = subprocess.Popen(["cec-client", "-s", "-d", "1"], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
                processedCommand = "tx " + format(PI, '01x') + format(processedDestination, '01x') + ":" + CecCommand.RIGHT
                (out, err) = cecClient.communicate(input=processedCommand)
            elif command == pb.TVMENU:
                cecClient = subprocess.Popen(["cec-client", "-s", "-d", "1"], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
                processedCommand = "tx " + format(PI, '01x') + format(processedDestination, '01x') + ":" + CecCommand.TVMENU
                (out, err) = cecClient.communicate(input=processedCommand)
            elif command == pb.DVDMENU:
                cecClient = subprocess.Popen(["cec-client", "-s", "-d", "1"], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
                processedCommand = "tx " + format(PI, '01x') + format(processedDestination, '01x') + ":" + CecCommand.DVDMENU
                (out, err) = cecClient.communicate(input=processedCommand)
            elif command == pb.AS:
                cecClient = subprocess.Popen(["cec-client", "-s", "-d", "1"], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
                processedCommand = "as"
                (out, err) = cecClient.communicate(input=processedCommand)
            elif command is pb.SLEEP:
                time.sleep(1.15)

    def onCecCommand(self, interest):
        self.log.debug("Received CEC command")
        # check command interest name
        # verify command interest
        message = pb.CommandMessage()
        ProtobufTlv.decode(message, interest.getName().get(3).getValue())
        self.loop.call_soon(self.processCommands, message)

        data = Data(interest.getName())
        data.setContent('ACK')
        return data

if __name__ == '__main__':
    node = CecTv()
    node.start()
