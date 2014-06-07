from pyndn import ThreadsafeFace
from pyndn.security import KeyChain
from app.discoveree import Discoveree
from app.cec_tv import CecTv
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

    cecTv = CecTv(loop, face, keyChain, discoveree)

    loop.run_forever()
    face.shutdown()

if __name__ == "__main__":
    main()
