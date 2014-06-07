from pyndn import ThreadsafeFace
from pyndn.security import KeyChain
# TODO: NFD hack: uncomment once NFD forwarding fixed
# from app.discoveree import Discoveree
# TODO: NFD hack: remove once NFD forwarding fixed
from app.local_discoveree import LocalDiscoveree
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

    # TODO: NFD hack: uncomment once NFD forwarding fixed
    # discoveree = Discoveree(loop, face, keyChain)
    # TODO: NFD hack: remove once NFD forwarding fixed
    discoveree = LocalDiscoveree(loop, face, keyChain)

    cecTv = CecTv(loop, face, keyChain, discoveree)

    loop.run_forever()
    face.shutdown()

if __name__ == "__main__":
    main()
