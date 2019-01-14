from flask import Flask
from apscheduler.schedulers.blocking import BlockingScheduler
from flask_cors import *
from flask_jsonrpc import JSONRPC
from contract_history import scan_block, get_info_result
import time



def job_1():
    print(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))
    time.sleep(10)

class Config(object):
    JOBS = [
        {
            'id': 'job2',
            'func': job_1,
            'args': (3, 4),
            'trigger': 'interval',
            'seconds': 5,
        }
    ]

app = Flask(__name__)
app.config.from_object(Config())
CORS(app, supports_credentials=True)
jsonrpc = JSONRPC(app, '/api')

@jsonrpc.method('hx.fdx.summary')
def index():
    return u'Welcome to Flask JSON-RPC'

@jsonrpc.method('hx.fdx.info')
def blockchain_info():
    return get_info_result()


if __name__ == '__main__':
    sched = BlockingScheduler()
    sched.add_job(job_1, 'interval', seconds=5)
    sched.start()

    app.run(host='0.0.0.0', debug=True) #use_reloader=False, prevent scheduler run twice
