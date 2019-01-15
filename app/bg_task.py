import threading
import time
from multiprocessing import Process, Lock
from apscheduler.schedulers.background import BackgroundScheduler
# from apscheduler.schedulers.blocking import BlockingScheduler


def job_1():
    print(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))

class BackgroundThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.process_lock = Lock()
        self.process_lock.acquire()
        self.thread_lock = threading.Lock()
        self.thread_lock.acquire()
        self.sched = BackgroundScheduler()
        self.sched.add_job(job_1, 'interval', seconds=5)

    def run(self):
        print "Starting background thread"
        self.sched.start()
        print "Exiting background thread"
    
    def __del__(self):
        self.process_lock.release()
        self.thread_lock.release()