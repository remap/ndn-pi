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

from pyndn.security.identity import IdentityManager
from pyndn.util.common import Common
from pyndn.util import Blob
from pyndn.name import Name
from iot_private_key_storage import IotPrivateKeyStorage
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
from pyndn.security.security_types import KeyType
from pyndn.security.certificate import IdentityCertificate, PublicKey, CertificateSubjectDescription
from pyndn.security.security_exception import SecurityException
import struct

class IotIdentityManager(IdentityManager):
    """
     Overrides the default constructor to force the use of our 
        IotPrivateKeyStorage
    """
    def __init__(self, identityStorage=None):
        super(IotIdentityManager, self).__init__(identityStorage, IotPrivateKeyStorage())
        
    def getPrivateKey(self, keyName):
        return self._privateKeyStorage.getPrivateKey(keyName)

    def addPrivateKey(self, keyName, keyDer):
        self._privateKeyStorage.addPrivateKey(keyName, keyDer)

    def _getNewKeyBits(self, keySize, progress_func=None):
        # returns public and private key DER in blobs
        key = RSA.generate(keySize, progress_func=progress_func)
        publicDer = key.publickey().exportKey(format='DER')
        privateDer = key.exportKey(format='DER', pkcs=8)
        return (Blob(publicDer, False), Blob(privateDer, False))
        

    def generateRSAKeyPair(self, identityName, isKsk=False, keySize=2048, progressFunc=None):
        """
        Generate a pair of RSA keys for the specified identity.
        
        :param Name identityName: The name of the identity.
        :param bool isKsk: (optional) true for generating a Key-Signing-Key 
          (KSK), false for a Data-Signing-Key (DSK). If omitted, generate a
          Data-Signing-Key.
        :param int keySize: (optional) The size of the key. If omitted, use a 
          default secure key size.
        :param function progressFunc: An update function taking a string 
            argument. See PyCrypto's RSA.generate for more information.
        :return: The generated key name.
        :rtype: Name
        """
        keyName = self._identityStorage.getNewKeyName(identityName, isKsk)
        publicBits, privateBits = self._getNewKeyBits(keySize, progressFunc)
        self._identityStorage.addKey(keyName, KeyType.RSA, publicBits)
        self._privateKeyStorage.addPrivateKey(keyName, privateBits)

        return keyName
        

    def generateRSAKeyPairAsDefault(self, identityName, isKsk=False, keySize=2048, progressFunc=None):
        """
        Generate a pair of RSA keys for the specified identity and set it as 
        default key for the identity.
        
        :param NameidentityName: The name of the identity.
        :param bool isKsk: (optional) true for generating a Key-Signing-Key 
          (KSK), false for a Data-Signing-Key (DSK). If omitted, generate a 
          Data-Signing-Key.
        :param int keySize: (optional) The size of the key. If omitted, use a 
          default secure key size.
        :param function progressFunc: An update function taking a string 
            argument. See PyCrypto's RSA.generate for more information
        :return: The generated key name.
        :rtype: Name
        """
        newKeyName = self.generateRSAKeyPair(identityName, isKsk, keySize, progressFunc)
        self._identityStorage.setDefaultKeyNameForIdentity(newKeyName)
        return newKeyName
    
    def selfSign(self, keyName):
        """
        Generate a self-signed certificate for a public key.
        
        :param Name keyName: The name of the public key.
        :return: The generated certificate.
        :rtype: IdentityCertificate
        """ 
        certificate = self.generateCertificateForKey(keyName)
        self.signByCertificate(certificate, certificate.getName())

        return certificate

    def generateCertificateForKey(self, keyName):
        # let any raised SecurityExceptions bubble up
        publicKeyBits = self._identityStorage.getKey(keyName)
        publicKeyType = self._identityStorage.getKeyType(keyName)
    
        publicKey = PublicKey(publicKeyType, publicKeyBits)

        timestamp = Common.getNowMilliseconds()
    
        # TODO: specify where the 'KEY' component is inserted
        # to delegate responsibility for cert delivery
        certificateName = keyName.getPrefix(-1).append('KEY').append(keyName.get(-1))
        certificateName.append("ID-CERT").append(Name.Component(struct.pack(">Q", timestamp)))        

        certificate = IdentityCertificate(certificateName)


        certificate.setNotBefore(timestamp)
        certificate.setNotAfter((timestamp + 30*86400*1000)) # about a month

        certificate.setPublicKeyInfo(publicKey)

        # ndnsec likes to put the key name in a subject description
        sd = CertificateSubjectDescription("2.5.4.41", keyName.toUri())
        certificate.addSubjectDescription(sd)

        certificate.encode()

        return certificate
        
    def encryptForIdentity(self, plaintext, identityName=None, keyName=None):
        """
        Encrypt the given bytes using the default key for the given identity,
        or the specfied key. If the key name is specified, the identity name is ignored.
        If there is no key or identity name given, a SecurityException is raised.
        :param plaintext: The data to encrypt
        :type plaintext: Blob
        :param Name identityName: (optional) The identity who will decrypt the message.
        :param Name keyName: (optional) The key used to encrypt the message.
        :return: The encrypted data
        :rtype: Blob
        """
        if keyName is None:
            keyName = self.getDefaultKeyNameForIdentity(identityName)
        keyDer = self._identityStorage.getKey(keyName)

        key = RSA.importKey(str(keyDer))
        cipher = PKCS1_OAEP.new(key)
        
        encrypted = Blob(cipher.encrypt(str(plaintext)), False)

        return encrypted

    def decryptAsIdentity(self, ciphertext, identityName=None, keyName=None):
        """
        Decrypt the given bytes using the default key for the given identity,
        or the specfied key. If the key name is specified, the identity name is ignored.
        If there is no key or identity name given, a SecurityException is raised.
        :param ciphertext: The data to decrypt
        :type ciphertext: Blob
        :param Name identityName: (optional) The identity the message is intended for.
        :param Name keyName: (optional) The key used to decrypt the message.
        :return: The decrypted data
        :rtype: Blob
        """
        if keyName is None:
            keyName = self.getDefaultKeyNameForIdentity(identityName)
        keyDer = self.getPrivateKey(keyName)
        key = RSA.importKey(str(keyDer))
        cipher = PKCS1_OAEP.new(key)
    
        decrypted = Blob(cipher.decrypt(str(ciphertext)), False)

        return decrypted
        
