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


import sys

from pyndn.security.policy import ConfigPolicyManager
from pyndn import Name

from pyndn.security.security_exception import SecurityException
from pyndn.util.boost_info_parser import BoostInfoParser

import os

"""
This module implements a simple hierarchical trust model that uses certificate
data to determine whether another signature/name can be trusted.

The policy manager enforces an environment, which corresponds to the network
prefix, i.e. the root of the network namespace.
All command interests must be signed with a certificate in this environment 
to be trusted.

There is a root name and public key which must be the top authority in the environment
for the certificate to be trusted. 
"""

class IotPolicyManager(ConfigPolicyManager):
    def __init__(self, identityStorage, configFilename=None):
        """
        :param pyndn.IdentityStorage: A class that stores signing identities and certificates.
        :param str configFilename: A configuration file specifying validation rules and network
            name settings.
        """

        # use the default configuration where possible
        # TODO: use environment variable for this, fall back to default
        path = os.path.dirname(__file__)
        templateFilename = os.path.join(path, '.default.conf')
        self._configTemplate = BoostInfoParser()
        self._configTemplate.read(templateFilename)

        if configFilename is None:
            configFilename = templateFilename

        super(IotPolicyManager, self).__init__(identityStorage, configFilename)
        self.setEnvironmentPrefix(None)
        self.setTrustRootIdentity(None)
        self.setDeviceIdentity(None)

    def updateTrustRules(self):
        """
        Should be called after either the device identity, trust root or network
        prefix is changed.

        Not called automatically in case they are all changing (typical for
        bootstrapping).

        Resets the validation rules if we don't have a trust root or enivronment

        """
        validatorTree = self._configTemplate["validator"][0].clone()

        if (self._environmentPrefix.size() > 0 and 
            self._trustRootIdentity.size() > 0 and 
            self._deviceIdentity.size() > 0):
            # don't sneak in a bad identity
            if not self._environmentPrefix.match(self._deviceIdentity):
                raise SecurityException("Device identity does not belong to configured network!")
            
            environmentUri = self._environmentPrefix.toUri()
            deviceUri = self._deviceIdentity.toUri()
             
            for rule in validatorTree["rule"]:
                ruleId = rule["id"][0].value
                if ruleId == 'Certificate Trust':
                    #modify the 'Certificate Trust' rule
                    rule["checker/key-locator/name"][0].value = environmentUri
                elif ruleId == 'Command Interests':
                    rule["filter/name"][0].value = deviceUri
                    rule["checker/key-locator/name"][0].value = environmentUri
            
        #remove old validation rules from config
        # replace with new validator rules
        self.config._root.subtrees["validator"] = [validatorTree]
        

    def inferSigningIdentity(self, fromName):
        """
        Used to map Data or Interest names to identitites.
        :param pyndn.Name fromName: The name of a Data or Interest packet
        """
        # works if you have an IotIdentityStorage
        return self._identityStorage.inferIdentityForName(fromName)

    def setTrustRootIdentity(self, identityName):
        """
        : param pyndn.Name identityName: The new identity to trust as the controller.
        """
        self._trustRootIdentity = Name(identityName)

    def getTrustRootIdentity(self):
        """
        : return pyndn.Name: The trusted controller's network name.
        """
        return self._trustRootIdentity

    def setEnvironmentPrefix(self, name):
        """
        : param pyndn.Name name: The new root of the network namespace (network prefix)
        """
        self._environmentPrefix = Name(name)

    def getEnvironmentPrefix(self):
        """
        :return: The root of the network namespace
        :rtype: pyndn.Name
        """
        return self._environmentPrefix

    def getDeviceIdentity(self):
        return self._deviceIdentity

    def setDeviceIdentity(self, identity):
        self._deviceIdentity = Name(identity)

    def hasRootCertificate(self):
        """
        :return: Whether we've downloaded the controller's network certificate
        :rtype: boolean
        """
        try:
            rootCertName = self._identityStorage.getDefaultCertificateNameForIdentity(
                    self._trustRootIdentity)
        except SecurityException:
            return False

        try:
            rootCert = self._identityStorage.getCertificate(rootCertName)
            if rootCert is not None:
                return True
        finally:
            return False

    def hasRootSignedCertificate(self):
        """
        :return: Whether we've received a network certificate from our controller
        :rtype: boolean
        """
        try:
            myCertName = self._identityStorage.getDefaultCertificateNameForIdentity(
                       self._deviceIdentity)
            myCert = self._identityStorage.getCertificate(myCertName)
            if self._trustRootIdentity.match(
                   myCert.getSignature().getKeyLocator().getKeyName()):
               return True
        except SecurityException:
           pass
       
        return False

    def removeTrustRules(self):
        """
        Resets the network prefix, device identity and trust root identity to
         empty values
        """
        self.setDeviceIdentity(None)
        self.setTrustRootIdentity(None)
        self.setEnvironmentPrefix(None)
        self.updateTrustRules()
