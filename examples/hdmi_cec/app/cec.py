
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

class CecCommand(object):
    STANDBY = "36"
    ON = "04"
    PLAY = "41:24"
    PAUSE = "41:25"
    FF = "41:05"
    RW = "41:09"
    SEL = "44:00"
    UP = "44:01"
    DOWN = "44:02"
    LEFT = "44:03"
    RIGHT = "44:04"
    TVMENU = "44:09"
    DVDMENU = "44:05"

    # TODO: volume controls not working

class CecDevice(object):
    TV = 0
    RECORDING_1 = 1
    RECORDING_2	= 2
    TUNER_1 = 3
    PLAYBACK_1 = 4
    AUDIO_SYSTEM = 5
    TUNER_2 = 6
    TUNER_3 = 7
    PLAYBACK_2 = 8
    PLAYBACK_3 = 9
    TUNER_4 = 10 
    PLAYBACK_3 = 11
    RESERVED_C = 12
    RESERVED_D = 13
    RESERVED_E = 14
    BROADCAST = 15

class CecStatus(object):
    def __init__(self):
        self._power = False

    def __repr__(self):
        return "CecStatus(power:{0})".format(self._power)
