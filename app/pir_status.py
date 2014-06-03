from pyndn import Exclude

class PirStatus(object):
    def __init__(self, pirId):
        self._pirId = pirId
        self._data = {}
        self._latestTimestamp = None
        self._exclude = Exclude()
        
    def addData(self, timestamp, value):
        if type(timestamp) is not long:
            return False
        if type(value) is not bool:
            return False
        if timestamp in self._data:
            return False
        self._data[timestamp] = value
        if timestamp > self._latestTimestamp:
            self._latestTimestamp = timestamp
        return True

    def getExclude(self):
        return self._exclude

    def setExcludeUpTo(self, exclude):
        self._exclude.clear()
        self._exclude.appendAny()
        self._exclude.appendComponent(exclude)

    def getLatestTimestamp(self):
        return self._latestTimestamp

    def getValueAt(self, timestamp):
        if timestamp in self._data:
            return self._data[timestamp]
        else:
            return None

    def getLatestValue(self):
        return self.getValueAt(self.getLatestTimestamp())

    def __repr__(self):
        return "{0} {1!s} {2!s} {3}".format(self._pirId, self._data, self._latestTimestamp, self._exclude.toUri())
