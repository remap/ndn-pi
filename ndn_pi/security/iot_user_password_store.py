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

import os
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Random import random
from sys import stderr
import base64
class IotUserPasswordStore(object):
    """
     This is a traditional (salted hash) password store, for general user 
     authentication, e.g. when using console to manage devices. The user
     private and public key pairs are maintained separately.

     This store is used by the controller only.
    """
    def __init__(self, passwordFile=None):
        if passwordFile is None:
            # NOTE: should this be in a system dir (e.g. /usr/local)?
            passwordFile = os.path.join(os.environ['HOME'], 'iot-tpm', 'user.passwd')
        self.passwordFile = passwordFile
        self.passwordStore = self.loadPasswords(passwordFile)

    def loadPasswords(self, fileName):
        passwords = {}
        try:
            with open(fileName, 'r') as pFile:
                for line in pFile:
                    try:
                        stripped = line.strip()
                        if len(stripped) == 0:
                            continue
                        userName, hashedPass = stripped.split()
                        passwords[userName] = hashedPass
                    except ValueError:
                        sys.stderr.write('Password file may be corrupted\n')
        except IOError:
            with open(fileName, 'w') as pFile:
               pass # create
        return passwords
                       
    def saveUserPassword(self, userName, password):
        nRuns = 1000
        salt = bytearray(16)
        for i in range(len(salt)):
            salt[i] = random.randint(0,0xff)

        hashedPass = PBKDF2(password, salt, count=nRuns)
        
        encodedSalt = base64.encode(salt)
        encodedPass = base64.encode(hashedPass)
        passStr =  ':'.join(str(nRuns), encodedSalt, encodedPass)

        self.passwordStore[userName] = passStr
        with open(self.passwordFile, 'w') as pFile:
            # rewrite everything in case of password change
            # TODO: may want to try just replacing the old
            pFile.write('{} {}\n', userName, passStr)


    def authenticateUser(self, userName, password):
        """ 
         Returns True if user is authenticated
        """
        authenticated = False
        try:
            storedVal = self.passwordStore[userName]
            runs, salt, hashedTruth = storedVal.split(':')
            hashedPass = PBKDF2(int(runs), password, salt)
            authenticated = (hashedPass == hashedTruth)
        finally:
            pass
        return authenticated

    def hasUsers(self):
        return len(self.passwordStore) > 0
