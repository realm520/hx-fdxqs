import click
from flask_cors import CORS
import os
import datetime
import logging
from app import create_app, db
from app.models import TxContractRawHistory, ServiceConfig, \
        TxContractEventHistory, ContractInfo, BlockRawHistory, ContractPersonExchangeOrder, \
        ContractPersonExchangeEvent, ContractExchangeOrder, \
        TxContractDealKdataWeekly, AccountInfo, TxContractDealKdata1Min, TxContractDealTick
from app.models import kline_table_list
from app.k_line_obj import KLine1MinObj, KLine5MinObj, KLine15MinObj, KLine30MinObj, KLine1HourObj, KLine2HourObj, \
        KLine6HourObj, KLine12HourObj, KLineWeeklyObj, KLineDailyObj, KLineMonthlyObj
from flask_migrate import Migrate
# from flask_apscheduler import APScheduler
from flask_jsonrpc import JSONRPC
from logging.handlers import TimedRotatingFileHandler


COV = None
if os.environ.get('FLASK_COVERAGE'):
    import coverage
    COV = coverage.coverage(branch=True, include='app/*')
    COV.start()

app = create_app(os.getenv('FLASK_CONFIG') or 'default')
cors = CORS(app, resources={r"/api": {"origins": "*"}})
migrate = Migrate(app, db)
# scheduler = APScheduler()
jsonrpc = JSONRPC(app, '/api', enable_web_browsable_api=True)


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
    data = ContractExchangeOrder.query.filter_by(address=addr, ex_pair=pair).\
            order_by(ContractExchangeOrder.id.desc()).paginate(page, page_count, False)
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


@jsonrpc.method('hx.fdxqs.exchange.kline.query(pair=str, type=int, count=int)', validate=True)
def exchange_bid_query(pair, type, count=100):
    if type < 0 or type >= len(kline_table_list):
        return {
            'error': 'invalid [type]'
        }
    now = datetime.datetime.now()
    start = now - datetime.timedelta(minutes=count)
    table = kline_table_list[type]
    data = table.query.filter(table.ex_pair==pair, table.timestamp>=start).\
            order_by(kline_table_list[type].id).all()
    return {
            'data': [t.toQueryObj() for t in data]
        }

'''
@jsonrpc.method('hx.fdxqs.exchange.coin.market()', validate=True)
def exchange_bid_query(pair, type, page=1, page_count=10):
    return {
            'total_records': data.total,
            'per_page': data.per_page,
            'total_pages': data.pages,
            'current_page': data.page,
            'data': [t.toQueryObj() for t in data.items]
        }
'''

@jsonrpc.method('hx.fdxqs.exchange.order.query(addr=str, pair=str, page=int, page_count=int)', validate=True)
def exchange_cancel_query(addr, pair, page=1, page_count=10):
    logging.info('[hx.fdxqs.exchange.order.query] - addr: %s, pair: %s, page: %d, page_count: %d' % (addr, pair, page, page_count))
    data = ContractExchangeOrder.query.filter_by(address=addr, ex_pair=pair).\
            order_by(ContractExchangeOrder.quote_amount/ContractExchangeOrder.base_amount).paginate(page, page_count, False)
    return {
            'total_records': data.total,
            'per_page': data.per_page,
            'total_pages': data.pages,
            'current_page': data.page,
            'data': [t.toQueryObj() for t in data.items]
        }


@app.shell_context_processor
def make_shell_context():
    return dict(app=app, db=db)


@app.cli.command('cleardb')
def dropdb():
    TxContractRawHistory.query.delete()
    # TxContractDealHistory.query.delete()
    BlockRawHistory.query.delete()
    TxContractEventHistory.query.delete()
    ServiceConfig.query.delete()
    ContractInfo.query.delete()
    ContractPersonExchangeOrder.query.delete()
    ContractPersonExchangeEvent.query.delete()
    ContractExchangeOrder.query.delete()
    TxContractDealTick.query.delete()
    AccountInfo.query.delete()
    for t in kline_table_list:
        t.query.delete()
    print("clear db finished")


@app.cli.command('rpc_test')
@click.argument('method')
@click.argument('args')
def rpc_test(method, args):
    from app.contract_history import ContractHistory
    ch = ContractHistory(app.config, db)
    rsp = ch.http_request(method, [args])
    print(str(rsp))


@app.cli.command('update_kline')
@click.option('--times', default=1, type=int, help='scan times')
def update_kline(times):
    from app.models import TxContractDealKdata5Min, TxContractDealKdata15Min, \
            TxContractDealKdata30Min, TxContractDealKdataDaily, TxContractDealKdata6Hour, \
            TxContractDealKdata1Hour, TxContractDealKdata2Hour, TxContractDealKdata12Hour, \
            TxContractDealKdataMonthly
    def process_kline_common(base_table, target_table, process_obj, pair='HC/HX'):
        k_last = target_table.query.filter_by(ex_pair=pair).order_by(target_table.block_num.desc()).first()
        k = process_obj(k_last)
        if k_last is None:
            last_block_num = 0
        else:
            last_block_num = k_last.block_num
        logging.info("%s: last block num: %d" % (str(target_table.__class__), last_block_num))
        ticks = base_table.query.filter(base_table.ex_pair==pair, base_table.block_num>=last_block_num).order_by(base_table.id).all()
        for t in ticks:
            k.process_tick(t)
        if k_last is not None:
            target_table.query.filter_by(block_num=k_last.block_num).delete()
        for r in k.get_k_data():
            db.session.add(target_table(ex_pair=pair, k_open=r['k_open'], k_close=r['k_close'], \
                    k_high=r['k_high'], k_low=r['k_low'], timestamp=r['start_time'], \
                    block_num=r['block_num'], base_amount=r['base_amount'], quote_amount=r['quote_amount']))

    # Process 1-minute K-Line
    process_kline_common(TxContractDealTick, TxContractDealKdata1Min, KLine1MinObj)
    # Process 5-minutes K-Line
    process_kline_common(TxContractDealKdata1Min, TxContractDealKdata5Min, KLine5MinObj)
    # Process 15-minutes K-Line
    process_kline_common(TxContractDealKdata1Min, TxContractDealKdata15Min, KLine15MinObj)
    # Process 30-minutes K-Line
    process_kline_common(TxContractDealKdata1Min, TxContractDealKdata30Min, KLine30MinObj)
    # Process 1-hour K-Line
    process_kline_common(TxContractDealKdata1Min, TxContractDealKdata1Hour, KLine1HourObj)
    # Process 2-hour K-Line
    process_kline_common(TxContractDealKdata1Hour, TxContractDealKdata2Hour, KLine2HourObj)
    # Process 6-hour K-Line
    process_kline_common(TxContractDealKdata1Hour, TxContractDealKdata6Hour, KLine6HourObj)
    # Process 12-hour K-Line
    process_kline_common(TxContractDealKdata1Hour, TxContractDealKdata12Hour, KLine12HourObj)
    # Process daily K-Line
    process_kline_common(TxContractDealKdata1Hour, TxContractDealKdataDaily, KLineDailyObj)
    # Process weekly K-Line
    process_kline_common(TxContractDealKdata1Hour, TxContractDealKdataWeekly, KLineWeeklyObj)
    # Process monthly K-Line
    process_kline_common(TxContractDealKdataDaily, TxContractDealKdataMonthly, KLineMonthlyObj)


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
