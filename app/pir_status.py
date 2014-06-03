# TODO: use bisect.insort instead of append

from pyndn import Exclude

class PirStatus(object):
    def __init__(self):
        self._data = []
        self._exclude = Exclude()
        
    def addData(self, timestamp, value):
        if type(timestamp) is not long:
            return False
        if type(value) is not bool:
            return False
        if not any(x[0] == timestamp for x in self._data):
            self._data.append((timestamp, value))
            return True
        else:
            return False

    def getExclude(self):
        return self._exclude

    def setExcludeUpTo(self, exclude):
        self._exclude.clear()
        self._exclude.appendAny()
        self._exclude.appendComponent(exclude)

    def getLastValue(self):
        if len(self._data):
            return self._data[-1][1]
        else:
            return None

    def __repr__(self):
        return "PirStatus(data:{0}, exclude:'{1}')".format(self._data, self._exclude.toUri())
