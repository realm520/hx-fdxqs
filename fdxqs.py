import click
import os
import logging
from app import create_app, db
from app.models import TxContractRawHistory, TxContractDealHistory, ServiceConfig, \
        TxContractEventHistory, ContractInfo, BlockRawHistory, ContractPersonExchangeOrder, \
        ContractPersonExchangeEvent, TxContractDealKdataHourly, TxContractDealKdataDaily, \
        TxContractDealKdataWeekly, AccountInfo
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


@app.cli.command('hello')
def hello():
    print("hello")


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


# @app.route('/user/<name>')
# def user(name):
#     return '<h1>Hello, %s!<h1>' % name


@jsonrpc.method('hx.fdxqs.exchange.deal.query(addr=str, pair=str, page=int, page_count=int)', validate=True)
def hx_fdxqs_exchange_deal_query(addr, pair, page=1, page_count=10):
    logging.info("[hx.fdxqs.exchange.deal.query] - addr: %s, pair: %s, offset: %d, limit: %d" % (addr, pair, page, page_count))
    data = TxContractDealHistory.query.filter_by(address=addr, ex_pair=pair).\
            order_by(TxContractDealHistory.id.desc()).paginate(page, page_count, False)
    return {
            'total_records': data.total,
            'per_page': data.per_page,
            'total_pages': data.pages,
            'current_page': data.page,
            'data': [t.toQueryObj() for t in data.items]
        }


@jsonrpc.method('hx.fdxqs.order.query(from_asset=str, to_asset=str, page=int, page_count=int)')
def hx_fdxqs_order_query(from_asset, to_asset, page=1, page_count=10):
    logging.info('[hx.fdxqs.order.query] - from_asset: %s, to_asset: %s, page: %d, page_count: %d' % (from_asset, to_asset, page, page_count))

    data = ContractPersonExchangeOrder.query.filter_by(from_asset=from_asset, to_asset=to_asset).\
            order_by(ContractPersonExchangeOrder.price).paginate(page, page_count, False)

    return {
            'total_records': data.total,
            'per_page': data.per_page,
            'total_pages': data.pages,
            'current_page': data.page,
            'data': [t.toQueryObj() for t in data.items]
        }


'''
@jsonrpc.method('hx.fdxqs.exchange.ask.query(addr=str, pair=str, offset=int, limit=int)', validate=True)
def exchange_bid_query(addr, pair, offset, limit):
    #print("addr: %s, pair: %s, offset: %d, limit: %d" % (addr, pair, offset, limit))
    return [{"addr": "aaaa", "pair": "HC/HX", "ask_count": 1, "bid_count": 2}]


@jsonrpc.method('hx.fdxqs.exchange.cancel.query(addr=str, pair=str, offset=int, limit=int)', validate=True)
def exchange_cancel_query(addr, pair, offset, limit):
    #print("addr: %s, pair: %s, offset: %d, limit: %d" % (addr, pair, offset, limit))
    return [{"addr": "aaaa", "pair": "HC/HX", "ask_count": 1, "bid_count": 2}]
'''

@app.shell_context_processor
def make_shell_context():
    return dict(app=app, db=db)


@app.cli.command('cleardb')
def dropdb():
    TxContractRawHistory.query.delete()
    TxContractDealHistory.query.delete()
    BlockRawHistory.query.delete()
    TxContractEventHistory.query.delete()
    ServiceConfig.query.delete()
    ContractInfo.query.delete()
    ContractPersonExchangeOrder.query.delete()
    ContractPersonExchangeEvent.query.delete()
    TxContractDealKdataHourly.query.delete()
    TxContractDealKdataDaily.query.delete()
    TxContractDealKdataWeekly.query.delete()
    AccountInfo.query.delete()
    print("clear db finished")


@app.cli.command('rpc_test')
@click.argument('method')
@click.argument('args')
def rpc_test(method, args):
    from app.contract_history import ContractHistory
    ch = ContractHistory(app.config, db)
    rsp = ch.http_request(method, [args])
    print(str(rsp))


@app.cli.command('scan_block')
@click.option('--times', default=1, type=int, help='scan times')
def scan_block(times):
    from app.contract_history import ContractHistory
    ch = ContractHistory(app.config, db)
    total = 0
    import time
    while total < times or times <= 0:
        ch.scan_block()
        time.sleep(5)
        total += 1
    print("scan block finished")


@app.cli.command('scan_person_exchange')
def scan_person_exchange():
    from app.contract_history import ContractHistory
    ch = ContractHistory(app.config, db)
    ch.exchange_person_orders(1)
    print("scan contract finished")


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
    app.run(host='0.0.0.0', port=80)
