# encoding=utf8
import os
import logging
from app import job_1
# from flask_cors import *
from flask_jsonrpc import JSONRPC
from flask_migrate import Migrate, upgrade
from app import scan_block
import time
from flask_apscheduler import APScheduler
from logging.handlers import TimedRotatingFileHandler
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import config


app = Flask(__name__)
app.config.from_object(config['default'])
db = SQLAlchemy(app)



scheduler = APScheduler()
# CORS(app, supports_credentials=True)
jsonrpc = JSONRPC(app, '/api')

@jsonrpc.method('hx.fdxqs.summary')
def index():
    return u'Welcome to Flask JSON-RPC'


@jsonrpc.method('hx.fdxqs.createdb')
def creat_db():
    return db.create_all()


@jsonrpc.method('hx.fdxqs.info')
def blockchain_info():
    return get_info_result()


@jsonrpc.method('hx.fdxqs.task.pause')
def pause_job(id):#暂停
    scheduler.pause_job(id)
    return "Success!"

@jsonrpc.method('hx.fdxqs.task.resume')
def resume_job(id):#恢复
    scheduler.resume_job(id)
    return "Success!"

@jsonrpc.method('hx.fdxqs.task.get(id=int)', validate=True)
def get_job(id) :#获取
    jobs=scheduler.get_jobs()
    current = ""
    for j in jobs:
        if int(j.id) == id:
            current = str(j.id)
    return current

@jsonrpc.method('hx.fdxqs.task.remove(id=int)', validate=True)
def remove_job(id):#移除
    jobs=scheduler.get_jobs()
    current = ""
    for j in jobs:
        if int(j.id) == id:
            scheduler.delete_job(j.id)
            current = str(j.id)
    return current

@jsonrpc.method('hx.fdxqs.task.add')
def add_job():
    scheduler.add_job(func=job_1, id='1', trigger='interval', seconds=5, replace_existing=True)
    return 'sucess'


if __name__ == '__main__':
    log_fmt = '%(asctime)s\tFile \"%(filename)s\",line %(lineno)s\t%(levelname)s: %(message)s'
    formatter = logging.Formatter(log_fmt)
    log_file_handler = TimedRotatingFileHandler(filename="hx_util_log", when="D", interval=1, backupCount=7)
    #log_file_handler.suffix = "%Y-%m-%d_%H-%M.log"
    #log_file_handler.extMatch = re.compile(r"^\d{4}-\d{2}-\d{2}_\d{2}-\d{2}.log$")
    log_file_handler.setFormatter(formatter)
    logging.basicConfig(level=logging.DEBUG)
    log = logging.getLogger()
    log.addHandler(log_file_handler)

    scheduler.init_app(app=app)
    scheduler.start()

    app.run(host='0.0.0.0', debug=True)
