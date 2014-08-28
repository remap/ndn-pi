#!/usr/bin/python
# -*- Mode:python; c-file-style:"gnu"; indent-tabs-mode:nil -*- */
#
# Copyright (C) 2014 Regents of the University of California.
# Author: Adeola Bannis
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

from __future__ import print_function
from ndn_pi.iot_node import IotNode
from ndn_pi.iot_controller import IotController
import sys

def print_usage():
    usageStr = 'Usage: iot_run [-h] [filename]\n'
    usageStr += '\t-h,--help\t\tPrint this message\n'
    usageStr += '\tfilename\t\tThe configuration file to load\n'
    print(usageStr)

def main():
    # I could use argparse, but I only have the one option...
    args = sys.argv[:]
    if '-h' in args or '--help' in args:
        print_usage()
        sys.exit(0)


    if len(args) > 2:
            print("Ignoring extra args: {}".format(' '.join(sys.argv[2:])), file=sys.stderr)
    elif len(args) > 1:
            fileName = args[1]
    else:
        print_usage()
        sys.exit(1)

    #peek at the config to see if we need to run as controller or as node
