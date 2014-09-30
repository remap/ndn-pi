# -*- Mode:python; c-file-style:"gnu"; indent-tabs-mode:nil -*- */
#
# Copyright (C) 2014 Regents of the University of California.
# Author: Adeola Bannis <abannis@ucla.edu>
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

"""
This module defines the IotUserKeyStorage class which manages passphrase-
encrypted (symmetric) user keys.
"""
from encryption_helper import EncryptionHelper
from Crypto.Hash import SHA256
from pyndn import Name
from pyndn.security import KeyType
from pyndn.util import Blob
import base64
import os
import sys

class IotUserKeyStorage(object):
    def __init__(self, keyDirectory=None):
        if keyDirectory is None:
            keyDirectory = os.path.join(os.environ['HOME'], '.ndn', 'iot-tpm')
        self._keyDir = keyDirectory

    def saveUserKey(self, userName, keyData, passphrase):
        """
        Encrypt the key with AES and save to the key directory
        :param Name userName: The user's identity
        :param Blob keyData: The key data to encrypt and store
        :param str passphrase: A user password for encrypting the key
        """
        userUri = userName.toUri()
        keyFile = self.nameTransform(userUri)
        hashedKey = SHA256.new(passphrase).digest()
        saveData = userUri+'\n'+keyData.toRawStr()
        encryptedData = EncryptionHelper.encrypt(saveData, hashedKey)
        encoded = base64.b64encode(encryptedData)

        with open(keyFile, 'w') as output:
            output.write(encoded)

    def doesUserKeyExist(self, userName):
        keyFile = self.nameTransform(userName.toUri())
        return os.path.isfile(self.keyFile)
        
    def hasAnyUsers(self):
        allFiles = os.listdir(self._keyDir)
        return len(allFiles) > 0

    def getUserKey(self, userName, passphrase):
        """
        Load the AES-encrypted key and decrypt it
        :param Name keyName: The user's identity
        :param str passphrase: A user password for encrypting the key
        :return: The decrypted key data
        :rtype: Blob
        """
        keyFile = self.nameTransform(userName.toUri())
        hashedKey = SHA256.new(passphrase).digest()
        keyData = None
        try:
            with open(keyFile, 'r') as encodedFile:
                encoded = encodedFile.read()
                encryptedKey = base64.b64decode(encoded)
                saveData = EncryptionHelper.decrypt(encryptedKey, hashedKey)
                
                parts = saveData.split('\n')
                retrievedName = Name(parts[0])
                if retrievedName.equals(userName):
                    keyData = parts[1]
        except:
            pass
         
        return Blob(keyData)

    def nameTransform(self, keyName):
        """
        Create a file path from keyName and the extension '.key'
        
        :param str keyName: The key name URI.
        :return: The file path.
        :rtype: str
        """
        hashInput = keyName
        if sys.version_info[0] > 2:
            # In Python 2.x, hash uses a str. Otherwise use Blob to convert.
            hashInput = Blob(keyName, False).toBuffer()        
        hash = SHA256.new(hashInput).digest()
        
        digest = base64.b64encode(hash)
        if type(digest) != str:
            # In Python 3, this is bytes, so convert to a str.
            digest = "".join(map(chr, digest))
        digest = digest.strip()
        digest = digest.replace('/', '%')

        return os.path.join(self._keyDir, digest + '.key')
