from tests.publish_pir import PirDataLogger

# TODO: don't hardcode, instead get from command interest
nodeType = "pir"

# TODO:
# obtain /home key from gateway
# check for keys
# if not keys, generate key for self
# trade keys with gateway
# register prefix /home/dev/<serial>/
# listen for <prefix>/command/pir/on or <prefix>/command/cec/off, etc.

if nodeType == "pir":
    logger = PirDataLogger(data_interval = 0.5) # sample at every 0.5 seconds (also affects face.processEvents)
    logger.run()
elif nodeType == "cec":
    # TODO: implement
    print "CEC stuff"
