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

"""
This module is based on the MemoryIdentityStorage class
"""
from pyndn.util import Blob
from pyndn.security.certificate import IdentityCertificate
from pyndn.security.security_exception import SecurityException
from pyndn import Name, Data
from pyndn.security.identity.identity_storage import IdentityStorage
import base64

class IotIdentityStorage(IdentityStorage):
    """
    Extend Memory Identity Storage to include the idea of default certs and keys
    """
    def __init__(self):
        super(IotIdentityStorage, self).__init__()
        # Maps identities to a list of associated keys
        self._keysForIdentity = {}

        # Maps keys to a list of associated certificates
        self._certificatesForKey = {}

        # The default identity in identityStore_, or "" if not defined.
        self._defaultIdentity = ""
        
        # The key is the keyName.toUri(). The value is the tuple 
        #  (KeyType keyType, Blob keyDer).
        self._keyStore = {}
        
        # The key is the key is the certificateName.toUri(). The value is the 
        #   encoded certificate.
        self._certificateStore = {}

    def doesIdentityExist(self, identityName):  
        """
        Check if the specified identity already exists.
        
        :param Name identityName: The identity name.
        :return: True if the identity exists, otherwise False.
        :rtype: bool
        """
        return identityName.toUri() in self._keysForIdentity
    
    def addIdentity(self, identityName):
        """
        Add a new identity. An exception will be thrown if the identity already 
        exists.

        :param Name identityName: The identity name.
        """
        identityUri = identityName.toUri()
        if identityUri in self._keysForIdentity:
            raise SecurityException("Identity already exists: " + identityUri)
  
        self._keysForIdentity[identityUri] = []
        
    def revokeIdentity(self, identityName):    
        """
        Revoke the identity. This will purge the associated keys and certificates from the stores.
        
        :param identityName: The identity to revoke. If it is the default, there will be no replacement.
        :type identityName: Name
        :return: True if the identity was revoked, False if not.
        :rtype: bool
        """
        identityUri = identityName.toUri()
        if identityUri in self._keysForIdentity:
            associatedKeys = self._keysForIdentity.pop(identityUri)
            for keyUri in associatedKeys:
                self.revokeKey(Name(keyUri))
            self._keysForIdentity.pop(identityUri)
            return True
        return False

    def doesKeyExist(self, keyName):    
        """
        Check if the specified key already exists.
        
        :param Name keyName: The name of the key.
        :return: True if the key exists, otherwise False.
        :rtype: bool
        """
        return keyName.toUri() in self._keyStore

    def addKey(self, keyName, keyType, publicKeyDer, asDefault=False):    
        """
        Add a public key to the identity storage.
        
        :param Name keyName: The name of the public key to be added.
        :param keyType: Type of the public key to be added.
        :type keyType: int from KeyType
        :param Blob publicKeyDer: A blob of the public key DER to be added.
        :param boolean asDefault: If set, this key becomes the default for the identity
        """
        identityName = keyName.getPrefix(-1)
        identityUri = identityName.toUri()
        if not self.doesIdentityExist(identityName):
            self.addIdentity(identityName)

        if self.doesKeyExist(keyName):
            raise SecurityException("A key with the same name already exists!")
  

        keyUri = keyName.toUri()
        self._keyStore[keyUri] = (keyType, Blob(publicKeyDer))
        # add the key to the list for the identity
        if asDefault:
            self._keysforIdentity[identityUri].insert(0, keyUri)
        else:
            self._keysForIdentity[identityUri].append(keyUri)
        self._certificatesForKey[keyUri] = []

    def getKey(self, keyName):    
        """
        Get the public key DER blob from the identity storage.
        
        :param Name keyName: The name of the requested public key.
        :return: The DER Blob. If not found, return a isNull() Blob.
        :rtype: Blob
        """
        keyNameUri = keyName.toUri()
        if not (keyNameUri in self._keyStore):
            # Not found.  Silently return a null Blob.
            return Blob()
        
        (_, publicKeyDer) = self._keyStore[keyNameUri]
        return publicKeyDer

    def getKeyType(self, keyName):    
        """
        Get the KeyType of the public key with the given keyName.
        
        :param Name keyName: The name of the requested public key.
        :return: The KeyType, for example KeyType.RSA.
        :rtype: an int from KeyType
        """
        keyNameUri = keyName.toUri()
        if not (keyNameUri in self._keyStore):
            raise SecurityException(
              "Cannot get public key type because the keyName doesn't exist")
        
        (keyType, _) = self._keyStore[keyNameUri]
        return keyType

    def revokeKey(self, keyName):
        keyUri = keyName.toUri()
        try:
            certificateList = self._certificatesForKey.pop(keyUri)
            for certificateUri in certificateList:
                self.revokeCertificate(Name(certificateUri))
            self._certificatesForKey.pop(keyUri)

            identityName = keyName.getPrefix(-1)
            self._keysForIdentity[identityName.toUri()].remove(keyUri)
            self._keyStore.pop(keyUri)
        except KeyError:
            raise SecurityException("Key does not exist")
        except ValueError:
            pass # key did not belong to its associated identity
        
    def doesCertificateExist(self, certificateName, exactMatch = False):    
        """
        Check if the specified certificate already exists.
        
        :param Name certificateName: The name of the certificate.
        :return: True if the certificate exists, otherwise False.
        :rtype: bool
        """
        if exactMatch:
            certificateUri = certificateName.toUri()
            return certificateUri in self._certificateStore
        else:
            versionName = self.findCertificateVersionForName(certificateName)
            return versionName is not None

    def findCertificateVersionForName(self, certificateName):
        """
        The certificate name given must be valid (have /KEY/ and /ID-CERT/ components)
        We return the first full certificate name that matches.
        """
        # we match up to the ID-CERT
        for compIdx in range(certificateName.size()):
            if certificateName.get(compIdx).toEscapedString() == 'ID-CERT':
                break
        
        # if it isn't there, this is a bad certificate name and we return None
        if certificateName.get(compIdx).toEscapedString() != 'ID-CERT':
            return None

        certificateName = certificateName.getPrefix(compIdx+1)
        for uri in self._certificateStore:
            if certificateName.match(Name(uri)):
                return uri

        return None
        
    def addCertificate(self, certificate, asDefault=False):    
        """
        Add a certificate to the identity storage.
        
        :param IdentityCertificate certificate: The certificate to be added. 
          This makes a copy of the certificate.
        :param boolean asDefault: If set, this certificate becomes the default for the key
        """
        certificateName = certificate.getName()
        keyName = certificate.getPublicKeyName()

        certificateUri = certificateName.toUri()
        keyUri = keyName.toUri()

        if not self.doesKeyExist(keyName):
            keyInfo = certificate.getPublicKeyInfo()
            self.addKey(keyName, keyInfo.getKeyType(), keyInfo.getKeyDer())

        # Check if the certificate has already exists.
        # We don't use the doesCertificateExist because this might be a new version
        if self.doesCertificateExist(certificateName, True):
            raise SecurityException("Certificate has already been installed!")

        # Check if the public key of certificate is the same as the key record.
        keyBlob = self.getKey(keyName)
        if (keyBlob.isNull() or 
              # Note: In Python, != should do a byte-by-byte comparison.
              keyBlob.toBuffer() != 
              certificate.getPublicKeyInfo().getKeyDer().toBuffer()):
            raise SecurityException(
              "Certificate does not match the public key!")
  
        # Insert the certificate.
        # wireEncode returns the cached encoding if available.
        self._certificateStore[certificateUri] = (
           certificate.wireEncode())

        # Map the key to the new certificate
        if asDefault:
            self._certificatesForKey[keyUri].insert(0, certificateUri)
        else:
            self._certificatesForKey[keyUri].append(certificateUri)


    def getCertificate(self, certificateName, allowAny = False):    
        """
        Get a certificate from the identity storage.
        
        :param Name certificateName: The name of the requested certificate.
        :param bool allowAny: (optional) If False, only a valid certificate will 
          be returned, otherwise validity is disregarded.  If omitted, 
          allowAny is False.
        :return: The requested certificate. If not found, return None.
        :rtype: Data
        """
        #TODO: check certificate validity
        certificateFullUri = self.findCertificateVersionForName(certificateName)
        if certificateFullUri is None:
            # Not found.  Silently return None.
            return None
  
        data = IdentityCertificate()
        data.wireDecode(self._certificateStore[certificateFullUri])
        return data

    def revokeCertificate(self, certificateName):
        """
        Must provide the full name of the certificate (timestamp included)
        """
        certificateUri = certificateName.toUri()
        try:
            certificate = self._certificateStore.pop(certificateUri)
        except KeyError:
            raise SecurityException("Certificate does not exist")
        else:
            keyName = IdentityCertificate.certificateNameToPublicKeyName(certificateName)
            self._certificatesForKey[keyName.toUri()].remove(certificateUri)

    #
    # Get/Set Default
    #

    def getDefaultIdentity(self):    
        """
        Get the default identity.
        
        :return: The name of default identity.
        :rtype: Name
        :raises SecurityException: if the default identity is not set.
        """
        if len(self._defaultIdentity) == 0:
            raise SecurityException("The default identity is not defined")
          
        return Name(self._defaultIdentity)

    def getDefaultKeyNameForIdentity(self, identityName):    
        """
        Get the default key name for the specified identity.
        
        :param Name identityName: The identity name.
        :return: The default key name.
        :rtype: Name
        :raises SecurityException: if the default key name for the identity is 
          not set.
        """
        if identityName is None:
            identityUri = self._defaultIdentity
        else:
            identityUri = identityName.toUri()

        if identityUri in self._keysForIdentity:
            # should not be any empty lists in here!
            keyList = self._keysForIdentity[identityUri]
            if len(keyList) > 0:
                return Name(keyList[0])
            else:
                raise SecurityException("No known keys for this identity.")
        else:
            raise SecurityException("Unknown identity")

    def getDefaultCertificateNameForKey(self, keyName):    
        """
        Get the default certificate name for the specified key.
        
        :param Name keyName: The key name.
        :return: The default certificate name.
        :rtype: Name
        :raises SecurityException: if the default certificate name for the key 
          name is not set.
        """
        keyUri = keyName.toUri()
        if keyUri in self._certificatesForKey:
            certList = self._certificatesForKey[keyUri]
            if len(certList) > 0:
                return Name(certList[0])
            else:
                raise SecurityException("No known certificates for this key")
        else:
            raise SecurityException("Unknown key name")


    def setDefaultIdentity(self, identityName):    
        """
        Set the default identity. If the identityName does not exist, then clear
        the default identity so that getDefaultIdentity() raises an exception.
        
        :param Name identityName: The default identity name.
        """
        identityUri = identityName.toUri()
        if identityUri in self._keysForIdentity:
            self._defaultIdentity = identityUri
        else:
            # The identity doesn't exist, so clear the default.
            self._defaultIdentity = ""

    def setDefaultKeyNameForIdentity(self, identityName, keyName):    
        """
        Set the default key name for the specified identity. The key must exist in the key store.
        
        :param Name keyName: The key name.
        :param Name identityName: (optional) The identity name to check the 
          keyName. If not set, the identity is inferred from the key name
        :raises SecurityException: if the key or identity does not exist
        """
        keyUri = keyName.toUri()
        identityUri = identityName.toUri()

        if identityUri in self._keysForIdentity:
            keyList = self._keysForIdentity[identityUri]
            if keyUri in keyList:
                keyIdx = keyList.index(keyUri)
                if keyIdx > 0:
                    # the first key is the default - nothing to do if the key is already first
                    keyList[keyIdx], keyList[0] = keyList[0], keyList[keyIdx]
            elif keyUri in self._keyStore:
                keyList.insert(0, keyUri)
            else:
                raise SecurityException("Unknown key name")
        else:
            raise SecurityException("Unknown identity name")

    def setDefaultCertificateNameForKey(self, keyName, certificateName):        
        """
        Set the default certificate name for the specified key. The certificate must exist in the certificate store.
                
        :param Name keyName: The key name.
        :param Name certificateName: The certificate name.
        :raises SecurityException: if the certificate or key does not exist
        """
        keyUri = keyName.toUri()
        certUri = certificateName.toUri()

        if keyUri in self._certificatesForKey:
            certList = self._certificatesForKey[keyUri]
            if certUri in certList:
                certIdx = certList.index(certUri)
                if certIdx > 0:
                    # the first key is the default - nothing to do if the key is already first
                    certList[certIdx], certList[0] = certList[0], certList[certIdx]
            elif certUri in self._certificateStore:
                certList.insert(0, certUri)
            else:
                raise SecurityException("Unnkown certificate name")
        else:
            raise SecurityException("Unknown key name")
    # --New methods--

    @staticmethod
    def loadIdentityCertificateFromFile(certFilename):
        # the file should contain a wireEncode()d IdentityCertificate
        with open(certFilename, 'r') as certStream:
            encodedCertLines = certStream.readlines()
            encodedCert = ''.join(encodedCertLines)
            certData = bytearray(base64.b64decode(encodedCert))
            cert = IdentityCertificate()
            cert.wireDecode(certData)
            return cert

    def getIdentitiesMatching(self, matchPrefix):
        matches = []
        for identityUri in self._keysForIdentity:
            if matchPrefix.match(Name(identityUri)):
                matches.append(identityUri)

        return matches

