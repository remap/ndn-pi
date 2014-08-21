
# -*- Mode:python; c-file-style:"gnu"; indent-tabs-mode:nil -*- */
#
# Copyright (C) 2014 Regents of the University of California.
# Author: Adeola Bannis <thecodemaiden@gmail.com>
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
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

from iot_node import IotNode
from iot_controller import IotController
from config.boost_info_parser import BoostInfoParser
import sys

def main(filename):
    # peek at the config to see if we are the controller
    config = BoostInfoParser()
    config.read(filename)
    deviceName = config["device/deviceName"]
    controllerName = config["device/controllerName"]
    if deviceName == controllerName:
        node = IotController(filename)
    else:
        node = IotNode(filename)
    node.start()

if __name__ == '__main__':
    try:
        filename = sys.argv[1]
        main(filename)
    except IndexError:
        print("Usage: {} <config-file>".format(__file__))

