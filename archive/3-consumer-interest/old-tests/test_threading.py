import time
from threading import Thread, Event

class MyThread(Thread):
    def __init__(self, event):
        Thread.__init__(self)
        self.stopped = event

    def run(self):
        while not self.stopped.wait(0.25):
            print "express interest"
            # call a function

stopFlag = Event()
thread = MyThread(stopFlag)
thread.start()
for i in range(0,100):
    print "process events"
    time.sleep(0.125)
# this will stop the timer
stopFlag.set()
