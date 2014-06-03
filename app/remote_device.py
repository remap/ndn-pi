from app.pir_status import PirStatus
from app.cec_status import CecStatus

class RemoteDevice(object):
    def __init__(self, type, id):
        self.type = type
        self.id = id
        if type == "pir":
            self.status = PirStatus()
        elif type == "cec":
            self.status = CecStatus()

    def __repr__(self):
        return "Device(type:{0}, id:{1}, status:{2})".format(self.type, self.id, self.status)
