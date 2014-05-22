def asdf():
    signature = hash data, timestamp, random number, AND secret barcode
    append signature to message

def onDataDevInit(interest, data):
    pass
    # verify data is signed by barcode
    data.getContent()
    # sign content (device's pub key) by gw-priv-key
    # publish to local repo

def onTimeout(interest):
    pass
    # resend interest once or twice?

# Some of these function args are probably not necessary
def onInterest(prefix, interest, transport, registeredPrefixId):
    # if interest.getName() matches "/home/gw/<serial>/<auth>"
        # do we have to verify interest signature?
        data = Data(Name("/home/gw/<serial>/<auth>"))
        data.setContent(public key)
        # send data

def onRegisterFailed(prefix):
    pass
    # try, try again

# generate root key
# name either "/home" or "/home/gw/<serial>"
# or maybe generate both (if we want multiple gateways, generate /home and /home/gw/<serial> and sign that by /home)
# then other gateways could get /home from first gateway

face = Face("localhost")
prefix = Name("/home/gw").append(serial)
face.registerPrefix(prefix, onInterest, onRegisterFailed)

# wait for device to come online
# HOW? Wait 30 sec?
# assume device already online
# receive barcode
# HOW? Wait for pipe? when you want to start a new device, run a program with barcode as arg

interest = Interest(Name("/home/dev").append(serial).append(<auth>))
# sign interest by barcode, can't use makeCommandInterest because that's async
face.expressInterest(interest, onDataDevInit, onTimeout)

# listen for <prefix> (will come from gateway)

# listen for <prefix>/command/pir/on or <prefix>/command/cec/off, etc.
if nodeType == "pir":
    logger = PirDataLogger(data_interval = 0.5) # sample at every 0.5 seconds (also affects face.processEvents)
    logger.run()
elif nodeType == "cec":
    # TODO: implement
    print "CEC stuff"
