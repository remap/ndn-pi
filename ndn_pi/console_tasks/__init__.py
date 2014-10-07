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

# Modified from whiptail.py, copyright (C) 2013 Marwan Alsabbagh
# https://github.com/marwano/whiptail
all = ['configure_gateway_task', 'connect_gateway_task', 'dialog',
        'pair_device_task', 'express_interest_task']

from configure_gateway_task import ConfigureGatewayTask
from pair_device_task import PairDeviceTask
from express_interest_task import ExpressInterestTask
from connect_gateway_task import ConnectGatewayTask
from Dialog import Dialog
