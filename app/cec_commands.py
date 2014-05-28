import time
import subprocess
import sys

devices = { "tv" : "0", "pi" : "1", "dvd" : "4", "reservede" : "e", "broadcast" : "f" }

commands = { "on" : "04", "standby" : "36", "play" : "41:24", "pause" : "41:25", "ff" : "41:05", "rw" : "41:09", "sel" : "44:00", "up" : "44:01", "down" : "44:02", "left" : "44:03", "right" : "44:04", "tvmenu" : "44:09", "dvdmenu" : "44:0b" } 
# ALL THESE MUST BE SENT TO DVD
# "ffmed" : "41:06", "ffmax" : "41:07"
# rw = fast reverse min
# couldn't get volume controls working

def sendTxCommand(dest, comm):
    try:
        destination = devices[dest]
    except KeyError:
        print "Unsupported dest"
        exit(1)
    try:
        command = commands[comm]
    except KeyError:
        print "Unsupported command"
        exit(1)
    input = "tx " + devices["pi"] + destination + ":" + command
    print input
    proc = subprocess.Popen(["cec-client", "-s", "-d", "1"], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    (out, err) = proc.communicate(input=input)
    print "OUT:", out
    print "ERR:", err

def sendCommand(command):
    print command
    proc = subprocess.Popen(["cec-client", "-s", "-d", "1"], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    (out, err) = proc.communicate(input=command)
    print "OUT:", out
    print "ERR:", err

def YOUSHALLNOTPASS():
    commandSeries = ["left", "wait 1", "sel", "wait 8", "right", "wait 1", "down", "wait 1", "down", "wait 1", "sel", "wait 4", "down", "wait 1", "sel", "wait 3", "ff", "ff", "ff", "wait 0.6", "play"]
    for c in commandSeries:
        if c.startswith("wait"):
            time.sleep(float(c.split()[1]))
        else:
            print c
            sendCommand("dvd", c)

if __name__ == "__main__":
    if len(sys.argv) == 1:
        YOUSHALLNOTPASS()
    elif len(sys.argv) == 2:
        sendCommand(sys.argv[1])
    elif len(sys.argv) == 3:
        # Single command mode
        sendTxCommand(sys.argv[1], sys.argv[2])
    else:
        print "Usage: python cec_commands.py [<device> <command>]\n<device>: tv|dvd|broadcast\n<command>: play|pause|ff|rw|sel|up|down|left|right\nIf no input, will queue Bridge of Khazad Dum\n"
        exit(1)
