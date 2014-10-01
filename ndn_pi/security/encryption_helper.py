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
from pyndn.encoding import WireFormat
from pyndn.util import Blob
from random import SystemRandom
from Crypto.Cipher import AES
from Crypto import Random
import base64
from hashlib import sha256
#from http://stackoverflow.com/questions/12524994/encrypt-decrypt-using-pycrypto-aes-256

class EncryptionHelper(object):
    BS=16
    @classmethod
    def pad(cls, arr):
        return arr + (cls.BS-len(arr) % cls.BS)*chr(cls.BS-len(arr)%cls.BS)

    @classmethod
    def unpad(cls, arr):
        return arr[0:-ord(arr[-1])]

    @classmethod
    def encrypt(cls, raw, key):
        raw = cls.pad(raw)
        iv = Random.new().read(AES.block_size)
        cipher = AES.new(key, AES.MODE_CBC, iv)
        return base64.b64encode(iv + cipher.encrypt(raw))

    @classmethod
    def decrypt(cls, encoded, key):
        encrypted = base64.b64decode(encoded)
        iv = encrypted[:AES.block_size]
        cipher = AES.new(key, AES.MODE_CBC, iv)
        return cls.unpad(cipher.decrypt(encrypted[AES.block_size:]))
