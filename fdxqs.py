import click
import os
import logging
from app import create_app, db
from app.models import TxContractRawHistory, TxContractDealHistory
from flask_migrate import Migrate
from flask_apscheduler import APScheduler
from flask_jsonrpc import JSONRPC
from logging.handlers import TimedRotatingFileHandler


COV = None
if os.environ.get('FLASK_COVERAGE'):
    import coverage
    COV = coverage.coverage(branch=True, include='app/*')
    COV.start()

app = create_app(os.getenv('FLASK_CONFIG') or 'default')
migrate = Migrate(app, db)
scheduler = APScheduler()
jsonrpc = JSONRPC(app, '/api')


log_fmt = '%(asctime)s\tFile \"%(filename)s\",line %(lineno)s\t%(levelname)s: %(message)s'
formatter = logging.Formatter(log_fmt)
log_file_handler = TimedRotatingFileHandler(filename="hx_util_log", when="D", interval=1, backupCount=7)
#log_file_handler.suffix = "%Y-%m-%d_%H-%M.log"
#log_file_handler.extMatch = re.compile(r"^\d{4}-\d{2}-\d{2}_\d{2}-\d{2}.log$")
log_file_handler.setFormatter(formatter)
logging.basicConfig(level=logging.INFO)
log = logging.getLogger()
log.addHandler(log_file_handler)
logging.getLogger("requests").setLevel(logging.WARNING)


@app.route('/')
def index():
    return '<h1>Hello World!</h1>'


@app.route('/user/<name>')
def user(name):
    return '<h1>Hello, %s!<h1>' % name


@jsonrpc.method('hx.fdxqs.summary')
def index():
    return u'Welcome to Flask JSON-RPC'


@jsonrpc.method('hx.fdxqs.info')
def blockchain_info():
    return get_info_result()


@jsonrpc.method('hx.fdxqs.task.pause')
def pause_job(id):
    scheduler.pause_job(id)
    return "Success!"

@jsonrpc.method('hx.fdxqs.task.resume')
def resume_job(id):
    scheduler.resume_job(id)
    return "Success!"

@jsonrpc.method('hx.fdxqs.task.get(id=int)', validate=True)
def get_job(id) :
    jobs=scheduler.get_jobs()
    current = ""
    for j in jobs:
        if int(j.id) == id:
            current = str(j.id)
    return current

@jsonrpc.method('hx.fdxqs.task.remove(id=int)', validate=True)
def remove_job(id):
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


@app.shell_context_processor
def make_shell_context():
    return dict(app=app, db=db, User=User, Role=Role)


@app.cli.command('initdb')
def initdb():
    db.create_all()
    print("init db finished")


@app.cli.command('scan_block')
def scan_block():
    from app.contract_history import ContractHistory
    ch = ContractHistory(app.config, db)
    ch.scan_block(500, 1003)
    print("scan block finished")



@app.cli.command()
@click.option('--coverage/--no-coverage', default=False, help='Enable code coverage')
def test(coverage):
    print('testing start...')
    if coverage and not os.environ.get('FLASK_COVERAGE'):
        import sys
        os.environ['FLASK_COVERAGE'] = '1'
        os.execvp(sys.executable, [sys.executable] + sys.argv)

    import unittest
    tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)

    if COV:
        COV.stop()
        COV.save()
        print('Coverage Summary:')
        COV.report()
        basedir = os.path.abspath(os.path.dirname(__file__))
        covdir = os.path.join(basedir, 'tmp/coverage')
        COV.html_report(directory=covdir)
        print('HTML version: file://%s/index.html' % covdir)
        COV.erase()


@app.cli.command()
def profile(length=25, profile_dir=None):
    from werkzeug.contrib.profiler import ProfilerMiddleware
    app.wsgi_app = ProfilerMiddleware(app.wsgi_app, restrictions=[length],
                                      profile_dir=profile_dir)
    app.run(host='0.0.0.0', debug=True)


if __name__ == '__main__':
    app.run()
