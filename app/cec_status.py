class CecStatus(object):
    def __init__(self):
        self._power = False

    def __repr__(self):
        return "CecStatus(power:{0})".format(self._power)
