import time
import subprocess
import sys

from app.cec import CecDevice, CecCommand

PI = CecDevice.RECORDING_1

def sendCommand(command):
    print command
    proc = subprocess.Popen(["cec-client", "-s", "-d", "1"], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    (out, err) = proc.communicate(input=command)
    print "OUT:", out
    print "ERR:", err

if __name__ == "__main__":
    if len(sys.argv) > 1:
        sendCommand(sys.argv[1:])
    else:
        command = "tx " + format(PI, '01x') + format(CecDevice.TV, '01x') + ":" + CecCommand.ON
        sendCommand(command)
