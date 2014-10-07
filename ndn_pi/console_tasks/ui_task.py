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
from dialog import Dialog
class UiTask(object):
    """
    The context of a task is a sequence containing a function to call and
    any arguments. This allows a 'back' functionality that maintains state.
    """
    def __init__(self, uiController, eventLoop, context, topContext=None):
        self.loop = eventLoop
        self.ui = uiController
        self.backContext = context
        self.topContext = topContext

    def pop(self):
        self.loop.call_soon(*self.backContext)

    def popAll(self):
        if self.topContext is not None:
            self.loop.call_soon(*self.topContext)
        else:
            self.pop()

    def run(self):
        pass # overidden by subclasses
