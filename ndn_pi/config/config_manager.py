
# -*- Mode:python; c-file-style:"gnu"; indent-tabs-mode:nil -*- */
#
# Copyright (C) 2014 Regents of the University of California.
# Author: Adeola Bannis
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


from whiptail_mod import Dialog
from boost_info_parser import BoostInfoParser, BoostInfoTree
import sys
import itertools
import re
from subprocess import Popen, PIPE
from subprocess import call as system_call
import os


class ConfigManager(Dialog):
    def __init__(self, fileName):
        super(ConfigManager, self).__init__()
        self.currentConfig = BoostInfoParser()

        pathName = os.path.dirname(os.path.abspath(__file__))
        self.baseFile = '/usr/local/etc/ndn_iot/default.conf'

        if fileName is None:
            self.inputFile = ''
            self.outputFile = 'config.conf'
            #load basic settings from template
            self.importDefaults()
        else:
            self.currentConfig.read(fileName)
            self.inputFile = self.outputFile = fileName

        self.width = 74
        self.height = 21
        self.title = 'NDN Network Configuration Utility'
        self.backtitle = 'F1 - Help\tEsc - Exit'
        self.auto_exit = False

        self.hasChanges = False

        self.optionsList = (('Edit newtork name settings', self.editNameInformation),
                            ('Edit command list', self.configureCommands),
                            #('Set certificate search directories', self.setCertDirectories), 
                            ('Regenerate device certificate', self.regenerateCertificate),
                            ('Save configuration', self.saveConfig), 
                            ('Load configuration', self.loadConfig),
                            #('Revert unsaved changes', self.reloadConfig),
                            ('Quit', self.quit))

    def importDefaults(self):
        self.currentConfig.read(self.baseFile)
        self.updateTrustRules()

    ###
    # Simple configuration
    ####
    def editNameInformation(self):
        environmentOptions = self.currentConfig["device"][0]

        networkPrefixNode = environmentOptions['environmentPrefix'][0]
        deviceNameNode = environmentOptions['deviceName'][0]
        controllerNameNode = environmentOptions['controllerName'][0]


        fields = []
        fields.append(Dialog.FormField('Network prefix', 
                networkPrefixNode.getValue().strip('/')))
        fields.append(Dialog.FormField('Device name', 
                deviceNameNode.getValue()))
        fields.append(Dialog.FormField('Controller name', 
                controllerNameNode.getValue())) 

        accept = False
        while not accept:
            retCode, values = self.form(formFieldInfo=fields, 
                    preExtras=['--hfile', 'help/DeviceName.help'])
            if retCode == self.DIALOG_CANCEL or retCode == self.DIALOG_ESC:
                break
            newNetworkPrefix = values[0].strip('/')
            newDeviceName = values[1].strip('/')
            newControllerName = values[2].strip('/')
            if len(newNetworkPrefix) == 0:
                #network name is empty
                self.alert("Network root cannot be /")
                continue
            elif newNetworkPrefix == 'localhost' or newNetworkPrefix == 'localhop':
                self.alert("Prefix {} is reserved".format(newNetworkPrefix))
                continue
            elif len(newDeviceName) == 0 or len(newControllerName) == 0:
                self.alert("Empty device/controller name is not allowed")
                continue
            else:
                accept = True

        if accept:
            networkPrefixNode.value = '/'+newNetworkPrefix
            deviceNameNode.value = newDeviceName
            controllerNameNode.value = newControllerName
            self.updateTrustRules()
            self.createCertificateIfNecessary()
            hasChanges = True # should we autosave?
    
    #####
    # Trust/security
    #####

    def updateTrustRules(self):
        # whenever the controller name changes, we must update the certificate
        # verification rule
        # when the device name changes, we must update the command interest rule
        networkName = self.currentConfig["device/environmentPrefix"][0].value
        deviceSuffix = self.currentConfig["device/deviceName"][0].value
        deviceName = '/'.join([networkName, deviceSuffix])

        trustRules = self.currentConfig["validator/rule"]
        for rule in trustRules:
            try:
                keyLocatorInfo = rule["checker/key-locator/name"][0]
            except KeyError, IndexError:
                # this rule did not use a key loactor, ignore
                pass
            else:
                keyLocatorInfo.value = networkName
                if rule["for"][0].value == "interest":
                    rule["filter/name"][0].value = deviceName
                    


    def regenerateCertificate(self):
        self.createCertificateIfNecessary(force=True)


    def createCertificateIfNecessary(self, force=False):
        # check ndn-sec output for a certificate for the requested identity
        # if absent, generate a new cert and put it in ~/.certs
        networkName = self.currentConfig["device/environmentPrefix"][0].value
        deviceSuffix = self.currentConfig["device/deviceName"][0].value
        deviceName = '/'.join([networkName, deviceSuffix])
        
        self.alert("Please wait, updating device certificates...", showButtons=False)

        nullFile = open(os.devnull, 'wb')

        # certificate is in stdout of ndnsec commands
        # save to disk and install if necessary (just generated)
        userCertDirectory = os.path.expanduser("~/.ndn/iot_certs")
        fileName = "default{}.cert".format(deviceName.replace('/', '_'))
        certName = os.path.join(userCertDirectory, fileName)
        try:
            os.makedirs(userCertDirectory)
            # may fail because it exists or can't be made, can't tell
        except:
            pass

        
        if not force:
            proc = Popen(["ndnsec", "cert-dump", "-i", deviceName], stdout=PIPE, 
                    stderr=nullFile)
            certData, err = proc.communicate()
        if force or proc.returncode == 1:
            # certificate (identity??) not found

            # TODO: why does this make the identity default, but not if typed
            # directly into the command line?!
            proc = Popen(["ndnsec" ,"key-gen", "-n", deviceName], stdout=PIPE, 
                    stderr=nullFile)
            certData, err = proc.communicate()
            if proc.returncode == 1:
                self.alert("ERROR!\nCannot create device certificates!")

        # save to file and install - installing the same cert twice is okay
        try:
            certFile = open(certName, 'w')
            certFile.write(certData)
            certFile.close()
            returncode = system_call(["ndnsec-cert-install", certName], 
                    stdout=nullFile, stderr=nullFile)
            if returncode != 0:
                self.alert("ERROR!\nCannot install device certificates!")
        except IOError:
            self.alert("ERROR!\nCannot save device certificates!")

        nullFile.close()

    ###
    # File management
    ###
    def saveConfig(self, *args):
        newOutputFile = self.prompt('Save configuration to:', self.outputFile).value
        if len(newOutputFile) == 0:
            return # cancel save
        try:
            self.createCertificateIfNecessary()
            self.currentConfig.write(newOutputFile)
            self.inputFile = self.outputFile = newOutputFile
        except IOError:
            self.alert("Cannot write configuration file {}".format(newOutputFile))

    def reloadConfig(self, *args):
        if self.inputFile is None:
            self.currentConfig = BoostInfoParser()
            self.importDefaults()
        else:
            try:
                newConfig = BoostInfoParser()
                newConfig.read(self.inputFile)
                self.currentConfig = newConfig
            except IOError:
                self.alert("Cannot read configuration file {}".format(self.inputFile))

    def loadConfig(self, *args):
        newInputFile = self.prompt('Load configuration from:', self.inputFile).value
        if len(newInputFile) == 0:
            return # cancel save
        try:
            newConfig = BoostInfoParser()
            newConfig.read(newInputFile)
            self.inputFile = self.outputFile = newInputFile
            self.currentConfig = newConfig
        except IOError:
            self.alert("Cannot read configuration file {}".format(newInputFile))

    ###
    # Command Interest setup
    ###
    def prepareCommandInfoFormFields(self, commandInfo):
        fields = []
        commandName = commandInfo["name"][0].getValue()
        functionName = commandInfo["functionName"][0].getValue()
        commandKeywords = commandInfo["keyword"]
        keywordList = ','.join([k.value for k in commandKeywords])
        try:
            commandInfo["authorize"]
            authStr = 'yes'
        except KeyError:
            authStr = 'no'

        fields.append(Dialog.FormField('Name', commandName))
        fields.append(Dialog.FormField('Function name', functionName))
        fields.append(Dialog.FormField('Keyword(s)', keywordList))
        fields.append(Dialog.FormField('Requires authentication',  authStr, 0))
        return fields


    def commandInsertEditForm(self, originalInfo):
        accept = False
        commandInfo = originalInfo.clone()
        while not accept:
            fields = self.prepareCommandInfoFormFields(commandInfo)
            retCode, values = self.form(formFieldInfo=fields, 
                     extraLabel='Toggle signed', 
                     preExtras=['--hfile', 'help/CommandEditor.help'])
        
            newName = values[0] if len(values) > 0 else ''
            newFuncName = values[1] if len(values) > 1 else ''
            newKeywords = values[2] if len(values) > 2 else ''
            if retCode == self.DIALOG_CANCEL or retCode == self.DIALOG_ESC:
                accept = True
                commandInfo = None
                break 

            commandInfo["name"][0].value = newName
            commandInfo["functionName"][0].value = newFuncName
            keywordList = re.split('\s*,\s*', newKeywords)
            # remove old keywords and add these
            commandInfo.subtrees["keyword"] = []
            for keyword in keywordList:
                commandInfo.createSubtree("keyword", keyword)

            if retCode == self.DIALOG_EXTRA:
                # toggle authorization state
                try:
                    commandInfo.subtrees.pop('authorize')
                except KeyError:
                    #wasn't authorized, authorize now
                    commandInfo.createSubtree('authorize')
            elif retCode == self.DIALOG_OK:
                # see if we are missing any info
                if len(newName) == 0 or len(newFuncName) == 0 or len(newKeywords) == 0:
                    self.alert("All values are required")
                elif re.match('^[a-zA-Z_][0-9a-zA-Z_]+$', newFuncName) is None:
                    self.alert("Function name is invalid")
                else:
                    accept = True
                    #wait - make sure we're not adding something that already exists!
                    try:
                        allCommands = self.currentConfig["device/command"]
                    except KeyError:
                        # there are no commands anyway
                        pass
                    else:
                        for command in allCommands:
                            if command["name"][0].value == newName and command is not originalInfo:
                                self.alert("Command already exists with that name!")
                                accept = False
                                break
                    if accept:
                        self.hasChanges = True
        return commandInfo
        

    def configureCommands(self):
        exit = False
        dummyName = '--- NO COMMANDS ---'
        while not exit:
            commandNameList = []
            try:
                # go straight to the source, not a copy
                allCommands = self.currentConfig["device"][0].subtrees["command"]
            except KeyError:
                pass
            else:
                for command in allCommands:
                    commandName = command["name"][0].getValue()
                    try:
                        authorizeFlag = command["authorize"][0].getValue()
                    except KeyError:
                        pass
                    else:
                        # the value should be empty, I'm just checking presence
                        commandName += "*"
                    commandNameList.append(commandName)

            if len(commandNameList) == 0:
                commandNameList = [dummyName]

            retCode, value = self.insertDeleteMenu('', commandNameList, 
                    deleteLabel='Delete', 
                    preExtras=['--hfile', 'help/CommandManager.help'])

            if value == dummyName and (retCode == self.DIALOG_OK or retCode == self.DIALOG_HELP):
                # can't edit/delete when there are no commands
                continue

            if retCode == self.DIALOG_EXTRA:
                # add
                commandInfo = BoostInfoTree()
                commandInfo.createSubtree("name", '')
                commandInfo.createSubtree("functionName", '')
                commandInfo.createSubtree("keyword", '')

                newCommand = self.commandInsertEditForm(commandInfo)
                if newCommand is not None:
                    node = self.currentConfig["device"][0]
                    node.addSubtree("command", newCommand)
            elif retCode == self.DIALOG_CANCEL or retCode==self.DIALOG_ESC:
                exit = True
            elif retCode == self.DIALOG_OK:
                idx = commandNameList.index(value)
                updatedInfo = self.commandInsertEditForm(allCommands[idx])
                if updatedInfo is not None:
                    allCommands[idx] = updatedInfo
                    updatedInfo.parent = self.currentConfig["device"][0]
            elif retCode == self.DIALOG_HELP:
                allCommands.pop(commandNameList.index(value))
                import pdb;

    ####
    # Set validator cert directories
    ####

    def setCertDirectories(self):
        dummyName = '--- NO DIRECTORIES --- '
        exit = False
        while not exit:
            allDirs = []
            trustAnchors = self.currentConfig["validator"][0].subtrees["trust-anchor"]
            for anchor in trustAnchors:
                if anchor["type"][0].value == 'dir':
                    allDirs.append(anchor["dir"][0].value)
            if len(allDirs) == 0:
                allDirs = [dummyName]
                
            # apparently having no 'ok' button wth an extra button messes 
            # up dialog's return codes...
            retCode, value = self.insertDeleteMenu('', allDirs, deleteLabel='Delete', 
                    editLabel='Add', insertLabel=None, 
                    preExtras=['--hfile', 'help/CertificateDirectory.help'])
            if value == dummyName and retCode == self.DIALOG_HELP:
                continue
            if retCode == self.DIALOG_CANCEL or retCode == self.DIALOG_ESC:
                exit = True
            elif retCode == self.DIALOG_OK:
                #add
                helpStr = u'\u2195'+"/Tab to change focus, Space to enter/select directory"
                retCode, newDir = self.fileSelection(msg=helpStr, directoriesOnly=True)
                if retCode == self.DIALOG_OK:
                    newAnchor = BoostInfoTree()
                    newAnchor.createSubtree("type", "dir")
                    newAnchor.createSubtree("dir", newDir)
                    newAnchor.createSubtree("refresh", "1h")
                    self.currentConfig["validator"][0].addSubtree("trust-anchor", newAnchor)
            elif retCode == self.DIALOG_HELP:
                #delete
                anchor = trustAnchors[allDirs.index(value)]
                trustAnchors.remove(anchor)
            
            
    ###
    # Main methods
    ###
    def quit(self):
        sys.exit(0)

    def createMainMenuItems(self):
        items = []
        environmentOptions = self.currentConfig["device"][0]
        i = 1

        for displayString, __ in self.optionsList:
            items.append((str(i), displayString))
            i += 1

        return items

    def displayMenu(self):
        menuItems = self.createMainMenuItems()
        toEdit = self.mainMenu('Select an option', menuItems ).value
        
        # on cancel, we get an empty string
        if len(toEdit) > 0:
            val = int(toEdit)-1
            if val < len(self.optionsList):
                dispatchFunc = self.optionsList[val][1]
                dispatchFunc()
        else: 
            self.quit()

    def main(self):
        while True:
            self.displayMenu()

    def quietMain(self):
        # just for generating certificates
        if len(self.inputFile) == 0:
            raise RuntimeError("No input file given")
        self.createCertificateIfNecessary()
        

