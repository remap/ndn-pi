# whiptail.py - Use whiptail to display dialog boxes from shell scripts
# Copyright (C) 2013 Marwan Alsabbagh
# Modified 2014 Adeola Bannis
# license: BSD, see LICENSE for more details.

from __future__ import print_function
import sys
import shlex
import itertools
from subprocess import Popen, PIPE
from collections import namedtuple
import os

__version__ = '0.1.dev'
PY3 = sys.version_info[0] == 3
string_types = str if PY3 else basestring
Response = namedtuple('Response', 'returncode value')


def flatten(data):
    return list(itertools.chain.from_iterable(data))

class Dialog(object):
    DIALOG_OK = DIALOG_YES = 0
    DIALOG_CANCEL = DIALOG_NO = 1
    DIALOG_HELP = 2
    DIALOG_EXTRA = 3
    DIALOG_ESC = 255

    def __init__(self, title='', backtitle='', height=10, width=50,
                 auto_exit=True):
        self.title = title
        self.backtitle = backtitle
        self.height = height
        self.width = width
        self.auto_exit = auto_exit

    def run(self, control, msg, preExtra= (), postExtra=(), exit_on=(1, 255)):
        cmd = ['dialog']

        if len(self.title) > 0:
            cmd.extend(['--title', self.title])

        if len(self.backtitle) > 0:
            cmd.extend(['--backtitle', self.backtitle])

        
        cmd.extend(list(preExtra))

        cmd.extend(['--'+control, msg , str(self.height), str(self.width)])
        cmd.extend(list(postExtra))

        p = Popen(cmd, stderr=PIPE)
        out, err = p.communicate()
        if self.auto_exit and p.returncode in exit_on:
            print('User cancelled operation.')
            sys.exit(p.returncode)
        toReturn = Response(p.returncode, err)
        return toReturn

    def prompt(self, msg, default='', password=False):
        control = 'passwordbox' if password else 'inputbox'
        return self.run(control, msg, postExtra=[default])

    def confirm(self, msg, default='yes'):
        defaultno = '--defaultno' if default == 'no' else ''
        return self.run('yesno', msg, postExtra=[defaultno], exit_on=[255]).returncode == 0

    def alert(self, msg, showButtons=True):
        if not showButtons:
            self.run('infobox', msg)
        else:
            self.run('msgbox', msg)

    def view_file(self, path):
        self.run('textbox', path, postExtra=['--scrolltext'])

    def calc_height(self, msg):
        height_offset = 8 if msg else 7
        return [str(self.height - height_offset)]

    def mainMenu(self, msg='', items=(), preExtras=(), prefix = ' ', postExtras=(),
                okLabel='Select'):
        allPreExtras = list(preExtras)
        allPreExtras.extend(['--nocancel', '--hfile', 'help/NDNConfig.help'])
        allPreExtras.extend(['--ok-label', okLabel])

        return self.menu(msg=msg, items=items, preExtras=allPreExtras, prefix=prefix, extras=postExtras)

    def insertDeleteMenu(self, msg='', items=(), preExtras=(), prefix = ' - ', postExtras=(),
            cancelLabel='Back', editLabel='Edit', insertLabel='Add', deleteLabel=None):
        # the ordering of buttons leaves something to be desired...
        allPreExtras = list(preExtras)

        if editLabel is None:
            allPreExtras.extend(['--no-ok'])
        else:
            allPreExtras.extend(['--ok-label', editLabel])

        if insertLabel is not None:
            allPreExtras.extend(['--extra-button', '--extra-label', insertLabel])

        if deleteLabel is not None:
            allPreExtras.extend(['--help-button', '--help-label', deleteLabel])

        allPreExtras.extend(['--cancel-label', cancelLabel])

        response = self.menu(msg=msg, items=items, 
                preExtras=allPreExtras, prefix=prefix, extras=postExtras)
        # remove the 'HELP' string from the help button respons
        if response.returncode == self.DIALOG_HELP:
            response = Response(response.returncode, response.value.strip('HELP '))
        return response


    def menu(self, msg='', items=(), preExtras = (), prefix = ' -  ', extras=()):
        if len(items) > 0:
            if isinstance(items[0], str):
                items = [(i, '') for i in items]
            else:
                items = [(k, prefix + v) for k,v in items]
        extra = self.calc_height(msg) + flatten(items)
        extra.extend(extras)
        return self.run('menu', msg, preExtras, extra)

    def showlist(self, control, msg, items, prefix):
        if isinstance(items[0], string_types):
            items = [(i, '', 'OFF') for i in items]
        else:
            items = [(k, prefix + v, s) for k, v, s in items]
        extra = self.calc_height(msg) + flatten(items)
        returnTuple = self.run(control, msg, postExtra=extra)
        return Response(returnTuple.returnCode, shlex.split(returnTuple.value))

    def radiolist(self, msg='', items=(), prefix=' - '):
        return self.showlist('radiolist', msg, items, prefix)

    def checklist(self, msg='', items=(), prefix=' - '):
        return self.showlist('checklist', msg, items, prefix)

    def fileSelection(self, msg='', startDirectory='./', preExtras=(), 
            postExtras=(), directoriesOnly=False):
        
        # some instructions are in order
        preExtras = list(preExtras)
        preExtras.extend(['--hline', msg])

        if directoriesOnly:
            commandName = 'dselect'
        else:
            commandName = 'fselect'
        returnCode, value = self.run(commandName, startDirectory, preExtras, postExtras)
        # handle incomplete directory names here
        # this is not the most user-friendly dialog
        while returnCode == self.DIALOG_OK:
            #sanitize the value
            if os.path.isdir(value):
                value = os.path.normpath(value)
                break
            elif len(value) > 0:
                if os.path.isdir(os.path.dirname(value)):
                    startDirectory = value
            returnCode, value = self.run(commandName, startDirectory, preExtras, postExtras)
        return Response(returnCode, value)

    def form(self, msg='', formFieldInfo=[], preExtras=(), postExtras=(), 
            margin=2, extraLabel= None):
        # compose form field information
        # first find the longest field, so we can align the input fields
        longestField = max(formFieldInfo, key=lambda x:len(x.label))
        inputStart = margin + len(longestField.label) + 2

        fields = []
        # now make the list of arguments
        y = 1 # don't jam the form into the top of the menu...
        for field in formFieldInfo:
            fields.extend([field.label, str(y), str(margin), 
                field.default, str(y), str(inputStart), 
                str(field.maxLength), str(field.maxLength)])
            y += 2

        postExtras = list(postExtras) 
        preExtras = list(preExtras)
        if extraLabel is not None:
            preExtras.extend(['--extra-button', '--extra-label', extraLabel])

        extra = self.calc_height(msg) + fields + postExtras
        response = self.run('form', msg, preExtras, extra)
        # similar to showlist, let's split up the return info for convenience
        response = Response(response.returncode, response.value.strip().split('\n'))
        return response
        

    class FormField(object):
        """ 
        Encapsulate the name, default value and maxLength of a field
        TODO: support non-editable fields if necessary
        """
        def __init__(self, label='', default='', maxLength=100):
            super(Dialog.FormField, self).__init__()
            self.label = label
            self.default = default
            self.maxLength = maxLength

