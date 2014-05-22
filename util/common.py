class Common(object):
    @staticmethod
    def getSerial():
        with open('/proc/cpuinfo') as f:
            for line in f:
                if line.startswith('Serial'):
                    return line.split(':')[1].strip()
