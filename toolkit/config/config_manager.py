
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
import os

# TODO: return a boolean retry from menu options?

class ConfigManager(Dialog):
    def __init__(self, fileName):
        super(ConfigManager, self).__init__()
        self.currentConfig = BoostInfoParser()
        self.configTemplate = BoostInfoParser()

        pathName = os.path.dirname(os.path.abspath(__file__))
        baseFile = os.path.join(pathName, '.base.conf')
        self.configTemplate.read(baseFile)

        if fileName is None:
            self.inputFile = None
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
                            ('Set certificate search directories', self.setCertDirectories), 
                            ('Regenerate certificate', self.regenerateCertificate),
                            ('Edit command list', self.configureCommands),
                            ('Save configuration', self.saveConfig), 
                            ('Load configuration', self.loadConfig),
                            ('Revert unsaved changes', self.reloadConfig),
                            ('Quit', self.quit))

    def importDefaults(self):
        # don't copy the template section
        configRoot = self.currentConfig.getRoot()

        deviceSettings = self.configTemplate["device"][0].clone()
        configRoot.addSubtree("device", deviceSettings)
        
        validatorSettings = self.configTemplate["validator"][0].clone()
        configRoot.addSubtree("validator", validatorSettings)

        self.updateCertificateTrustRule()

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
            retCode, values = self.form(formFieldInfo=fields)
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
            self.updateCertificateTrustRule()
            hasChanges = True # should we autosave?
            

    def updateCertificateTrustRule(self):
        # whenever the controller name changes, we must update the certificate
        # verification rule
        networkName = self.currentConfig["device/environmentPrefix"][0].getValue()
        controllerName = self.currentConfig["device/controllerName"][0].getValue()
        controllerName = '/'.join([networkName, controllerName])
        #also have to replace it in 'Certificate Trust' rule
        trustRules = self.currentConfig["validator/rule"]
        for rule in trustRules:
            if (rule["for"][0].getValue() == "data" and
                    rule["id"][0].getValue() == "Certificate Trust"):
                keyLocatorName = rule["checker/key-locator/name"][0]
                keyLocatorName.value = controllerName
                break # should not be more than one matching rule

    def regenerateCertificate(self):
        pass

    ###
    # File management
    ###
    def saveConfig(self, *args):
        newOutputFile = self.prompt('Save configuration to:', self.outputFile).value
        if len(newOutputFile) == 0:
            return # cancel save
        try:
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
        try:
            commandInfo["authorize"]
            authStr = 'yes'
        except KeyError:
            authStr = 'no'

        fields.append(Dialog.FormField('Name', commandName))
        fields.append(Dialog.FormField('Function name', functionName))
        fields.append(Dialog.FormField('Requires authentication',  authStr, 0))
        return fields

    def commandInsertEditForm(self, commandInfo):
        # Assume we are inserting if the commandInfo is None
        accept = False
        while not accept:
            fields = self.prepareCommandInfoFormFields(commandInfo)
            retCode, values = self.form(formFieldInfo=fields, 
                     extraLabel='Toggle signed')
        
            newName = values[0] if len(values) > 0 else ''
            newFuncName = values[1] if len(values) > 1 else ''
            if retCode == self.DIALOG_CANCEL or retCode == self.DIALOG_ESC:
                accept = True
                commandInfo = None
                break 

            commandInfo["name"][0].value = newName
            commandInfo["functionName"][0].value = newFuncName
            if retCode == self.DIALOG_EXTRA:
                # toggle authorization state
                try:
                    commandInfo.subTrees.pop('authorize')
                except KeyError:
                    #wasn't authorized, authorize now
                    commandInfo.createSubtree('authorize')
            elif retCode == self.DIALOG_OK:
                # see if we are missing any info
                if len(newName) == 0 or len(newFuncName) == 0:
                    self.alert("All values are required")
                elif re.match('^[a-zA-Z_][0-9a-zA-Z_]+$', newFuncName) is None:
                    self.alert("Function name is invalid")
                else:
                    accept = True
                    #wait - make sure we're not adding something that already exists!
                    try:
                        allCommands = commandInfo.parent["command"]
                    except KeyError:
                        # there are no commands anyway
                        pass
                    else:
                        for command in allCommands:
                            if command["name"][0].value == newName and command is not commandInfo:
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
                allCommands = self.currentConfig["device/command"]
            except KeyError:
                commandNameList = [dummyName]
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

            retCode, value = self.insertDeleteMenu('', commandNameList, deleteLabel='Delete')

            if value == dummyName and (retCode == self.DIALOG_OK or retCode == self.DIALOG_HELP):
                continue

            # locate the selected value in case we need it

            if retCode == self.DIALOG_EXTRA:
                # add
                commandInfo = BoostInfoTree()
                commandInfo.createSubtree("name", '')
                commandInfo.createSubtree("functionName", '')
                commandInfo.parent = self.currentConfig["device"][0]

                newCommand = self.commandInsertEditForm(commandInfo)
                if newCommand is not None:
                    node = self.currentConfig["device"][0]
                    node.addSubtree("command", newCommand)
            elif retCode == self.DIALOG_CANCEL or retCode==self.DIALOG_ESC:
                exit = True
            elif retCode == self.DIALOG_OK:
                info = allCommands[commandNameList.index(value)]
                self.commandInsertEditForm(info)
            elif retCode == self.DIALOG_HELP:
                info = allCommands[commandNameList.index(value)]
                #DELETEDDDD
                parentNode = info.parent
                allCommands = parentNode.subTrees['command']
                allCommands.remove(info)
                if len(allCommands) == 0:
                    parentNode.subTrees.pop('command')

    ####
    # Set validator cert directories
    ####
    def addCertDirectory(self):
        retCode, newDir = self.fileSelection(directoriesOnly=True)


    def setCertDirectories(self):
        dummyName = '--- NO VERIFICATION --- '
        exit = False
        while not exit:
            allDirs = []
            trustAnchors = self.currentConfig["validator/trust-anchor"]
            for anchor in trustAnchors:
                if anchor["type"][0].value == 'dir':
                    allDirs.append(anchor["dir"][0].value)
            if len(allDirs) == 0:
                allDirs = [dummyName]
                
            retCode, value = self.insertDeleteMenu('', allDirs, deleteLabel='Delete', editLabel=None)
            if value == dummyName and retCode == self.DIALOG_HELP:
                continue

            if retCode == self.DIALOG_CANCEL or retCode == self.DIALOG_ESC:
                exit = True
            elif retCode == self.DIALOG_EXTRA:
                #add
                pass
            elif retCode == self.DIALOG_HELP:
                #delete
                anchor = trustAnchors[allDirs.index(value)]
            
            
    ###
    # Other methods
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

if __name__ == '__main__':
    ConfigManager(None).main()
