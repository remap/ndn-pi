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
This module defines the IotPrivateKeyStorage class which extends 
FilePrivateKeyStorage to implement private key storage using files.
"""

import os
import sys
import base64
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from pyndn.util import Blob
from pyndn.security.security_types import DigestAlgorithm
from pyndn.security.security_types import KeyClass
from pyndn.security.security_types import KeyType
from pyndn.security.security_exception import SecurityException
from pyndn.security.identity.file_private_key_storage import FilePrivateKeyStorage

class IotPrivateKeyStorage(FilePrivateKeyStorage):

    def sign(self, data, keyName, digestAlgorithm = DigestAlgorithm.SHA256):
        """
        Fetch the private key for keyName and sign the data, returning a 
        signature Blob.

        :param data: Pointer the input byte buffer to sign.
        :type data: An array type with int elements
        :param Name keyName: The name of the signing key.
        :param digestAlgorithm: (optional) the digest algorithm. If omitted,
          use DigestAlgorithm.SHA256.
        :type digestAlgorithm: int from DigestAlgorithm
        :return: The signature, or an isNull() Blob pointer if signing fails.
        :rtype: Blob
        """
        if digestAlgorithm != DigestAlgorithm.SHA256:
            raise SecurityException(
              "FilePrivateKeyStorage.sign: Unsupported digest algorithm")

        der = self.getPrivateKey(keyName)
        privateKey = RSA.importKey(der.toRawStr())
        
        # Sign the hash of the data.
        if sys.version_info[0] == 2:
            # In Python 2.x, we need a str.  Use Blob to convert data.
            data = Blob(data, False).toRawStr()
        signature = PKCS1_v1_5.new(privateKey).sign(SHA256.new(data))
        # Convert the string to a Blob.
        return Blob(bytearray(signature), False)

    def doesKeyExist(self, keyName, keyClass):
        """
        Check if a particular key exists.
        
        :param Name keyName: The name of the key.
        :param keyClass: The class of the key, e.g. KeyClass.PUBLIC, 
           KeyClass.PRIVATE, or KeyClass.SYMMETRIC.
        :type keyClass: int from KeyClass
        :return: True if the key exists, otherwise false.
        :rtype: bool
        """
        keyURI = keyName.toUri()
        if keyClass == KeyClass.PUBLIC:
            return os.path.isfile(self.nameTransform(keyURI, ".pub"))
        elif keyClass == KeyClass.PRIVATE:
            return os.path.isfile(self.nameTransform(keyURI, ".pri"))
        elif keyClass == KeyClass.SYMMETRIC:
            return os.path.isfile(self.nameTransform(keyURI, ".key").c_str())
        else:
            return False

    def addPrivateKey(self, keyName, keyDer):
        """
        Add a private key to the store.
        :param Name keyName: The name of the key
        :param Blob keyDer: The private key DER
        """ 
        if self.doesKeyExist(keyName, KeyClass.PRIVATE):
            raise SecurityException("The private key already exists!")
        keyUri = keyName.toUri()
        newPath = self.nameTransform(keyUri, ".pri")

        encodedDer = base64.b64encode(keyDer.toRawStr())
        with open(newPath, 'w') as keyFile:
            keyFile.write(encodedDer)

    def getPrivateKey(self, keyName):
        """
        Fetch a private key from the store.
        :param Name keyName: The name of the private key to look up.
        :return: The binary DER encoding of the private key bits
        :rtype: Blob
        """
        keyURI = keyName.toUri()

        if not self.doesKeyExist(keyName, KeyClass.PRIVATE):
            raise SecurityException(
              "FilePrivateKeyStorage.sign: private key doesn't exist")

        # Read the private key.
        base64Content = None
        with open(self.nameTransform(keyURI, ".pri")) as keyFile:
            base64Content = keyFile.read()
        der = base64.b64decode(base64Content)

        return Blob(der)
