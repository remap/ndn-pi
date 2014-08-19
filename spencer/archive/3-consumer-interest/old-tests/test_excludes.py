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
from pyndn import Face
from pyndn import Interest
from pyndn import Exclude

import json

callbacks = 0
exclude = Exclude()

def onData(interest, data):
    global callbacks
    callbacks += 1
    print "Interest:", interest.getName().toUri(), "data:", data.getName().toUri(), "content:", data.getContent().toRawStr()
    print data.getName().get(len(data.getName())-1).toEscapedString()
    exclude.appendComponent(data.getName().get(len(data.getName())-1).toEscapedString())
#    exclude.appendComponent(data.getName().getSubName(len(data.getName())-1).toUri())

def onTimeout(interest):
    global callbacks
    callbacks += 1
    print "Timeout:", interest.getName().toUri()

face = Face("localhost")
interest = Interest(Name("/home/pir"))
print "Interest:", interest.getName().toUri()
print "\tExcludes:", interest.getExclude().toUri()
face.expressInterest(interest, onData, onTimeout)

while callbacks < 1:
    face.processEvents()
    time.sleep(0.01)

interest = Interest(Name("/home/pir"))
interest.setExclude(exclude)
print "Interest:", interest.getName().toUri()
print "\tExcludes:", interest.getExclude().toUri()
face.expressInterest(interest, onData, onTimeout)

while callbacks < 2:
    face.processEvents()
    time.sleep(0.01)

interest = Interest(Name("/home/pir"))
interest.setExclude(exclude)
print "Interest:", interest.getName().toUri()
print "\tExcludes:", interest.getExclude().toUri()
face.expressInterest(interest, onData, onTimeout)

while callbacks < 3:
    face.processEvents()
    time.sleep(0.01)
