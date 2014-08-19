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

# TODO: use bisect.insort instead of append

from pyndn import Exclude

class PirStatus(object):
    def __init__(self):
        self._data = []
        self._exclude = Exclude()
        
    def addData(self, timestamp, value):
        if type(timestamp) is not long:
            return False
        if type(value) is not bool:
            return False
        if not any(x[0] == timestamp for x in self._data):
            self._data.append((timestamp, value))
            return True
        else:
            return False

    def getExclude(self):
        return self._exclude

    def setExcludeUpTo(self, exclude):
        self._exclude.clear()
        self._exclude.appendAny()
        self._exclude.appendComponent(exclude)

    def getLastValue(self):
        if len(self._data):
            return self._data[-1][1]
        else:
            return None

    def __repr__(self):
        return "PirStatus(data:{0}, exclude:'{1}')".format(self._data, self._exclude.toUri())
