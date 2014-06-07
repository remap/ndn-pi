from pyndn import ThreadsafeFace
from pyndn.security import KeyChain
from app.discoveree import Discoveree
from app.pir_publisher import PirPublisher
try:
    import asyncio
except ImportError:
    import trollius as asyncio
import logging
logging.basicConfig(level=logging.INFO)

def main():
    loop = asyncio.get_event_loop()
    face = ThreadsafeFace(loop, "localhost")
    keyChain = KeyChain()
    face.setCommandSigningInfo(keyChain, keyChain.getDefaultCertificateName())

    discoveree = Discoveree(loop, face, keyChain)
    pirPublisher = PirPublisher(loop, face, keyChain, discoveree, 12)
    pirPublisher = PirPublisher(loop, face, keyChain, discoveree, 7)

    loop.run_forever()
    face.shutdown()

if __name__ == "__main__":
    main()
