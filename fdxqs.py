import click
import os
import datetime
import logging
from app import create_app, db
from app.models import TxContractRawHistory, ServiceConfig, \
        TxContractEventHistory, ContractInfo, BlockRawHistory, ContractPersonExchangeOrder, \
        ContractExchangeOrder, TxContractDealHistory, \
        TxContractDealKdataWeekly, AccountInfo, TxContractDealKdata1Min, TxContractDealTick
from app.models import kline_table_list, TxContractDepositWithdraw, ContractExchangePair
from app.k_line_obj import KLine1MinObj, KLine5MinObj, KLine15MinObj, KLine30MinObj, KLine1HourObj, KLine2HourObj, \
        KLine6HourObj, KLine12HourObj, KLineWeeklyObj, KLineDailyObj, KLineMonthlyObj
from app.contract_history import ContractHistory
from flask_migrate import Migrate
# from flask_apscheduler import APScheduler
from flask_jsonrpc import JSONRPC
from flask_cors import cross_origin, CORS
from flask import make_response
from logging.handlers import TimedRotatingFileHandler



COV = None
if os.environ.get('FLASK_COVERAGE'):
    import coverage
    COV = coverage.coverage(branch=True, include='app/*')
    COV.start()

app = create_app(os.getenv('FLASK_CONFIG') or 'default')
CORS(app)
migrate = Migrate(app, db)
# scheduler = APScheduler()


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

@cross_origin
@app.route('/api', methods=['OPTIONS'])
def options_api():
    rst = make_response('')
    rst.headers['Access-Control-Allow-Origin'] = '*'
    rst.headers['Access-Control-Allow-Methods'] = 'PUT,GET,POST,DELETE,OPTIONS'
    allow_headers = "Referer,Accept,Origin,User-Agent,Content-Type,X-TOKEN"
    rst.headers['Access-Control-Allow-Headers'] = allow_headers
    return rst

jsonrpc = JSONRPC(app, '/api', enable_web_browsable_api=True)


@jsonrpc.method('hx.fdxqs.exchange.deposit.withdraw.query(addr=str, symbol=str, page=int, page_count=int)', validate=True)
def hx_fdxqs_exchange_deposit_withdraw_query(addr, symbol, page=1, page_count=10):
    logging.info("[hx.fdxqs.exchange.deal.query] - addr: %s, symbol: %s, offset: %d, limit: %d" % (addr, symbol, page, page_count))
    if len(symbol) > 0:
        data = TxContractDepositWithdraw.query.filter_by(address=addr, asset_symbol=symbol).\
                order_by(TxContractDepositWithdraw.block_num.desc()).paginate(page, page_count, False)
    else:
        data = TxContractDepositWithdraw.query.filter_by(address=addr).\
                order_by(TxContractDepositWithdraw.block_num.desc()).paginate(page, page_count, False)
    return {
            'total_records': data.total,
            'per_page': data.per_page,
            'total_pages': data.pages,
            'current_page': data.page,
            'data': [t.toQueryObj() for t in data.items]
        }


@jsonrpc.method('hx.fdxqs.exchange.order.query(addr=str, pair=str, page=int, page_count=int)', validate=True)
def hx_fdxqs_exchange_order_query(addr, pair, page=1, page_count=10):
    """
    Query all orders by address
    """
    logging.info("[hx.fdxqs.exchange.order.query] - addr: %s, pair: %s, offset: %d, limit: %d" % (addr, pair, page, page_count))
    data = ContractExchangeOrder.query.filter_by(address=addr, ex_pair=pair).\
            order_by(ContractExchangeOrder.timestamp.desc()).paginate(page, page_count, False)
    return {
            'total_records': data.total,
            'per_page': data.per_page,
            'total_pages': data.pages,
            'current_page': data.page,
            'data': [t.toQueryObj() for t in data.items]
        }


@jsonrpc.method('hx.fdxqs.exchange.deal.query(pair=str, count=int)', validate=True)
def hx_fdxqs_exchange_deal_query(pair, count=10):
    """
    Query all orders by address
    """
    logging.info("[hx.fdxqs.exchange.deal.query] - pair: %s, count: %d" % (pair, count))
    data = TxContractDealHistory.query.filter_by(ex_pair=pair).\
            order_by(TxContractDealHistory.timestamp.desc()).limit(count).all()
    return {
            'data': [t.toQueryObj() for t in data]
        }


@jsonrpc.method('hx.fdxqs.otc.order.query(from_asset=str, to_asset=str, page=int, page_count=int)')
def hx_fdxqs_otc_order_query(from_asset, to_asset, page=1, page_count=10):
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
def hx_fdxqs_kline_query(pair, type, count=100):
    """
    @param type - kline cycle type (0: 1-min, 1: 5-min, 2: 15-min, 3: 30-min, 4: 1-hour, 5: 2-hour, 6: 6-hour, 7: 12-hour, 8: 1-day, 9: 1-week, 10: 1-month)
    """
    import copy
    if type < 0 or type >= len(kline_table_list):
        return {
            'error': 'invalid [type]'
        }
    cycles = [60, 300, 900, 1800, 3600, 7200, 21600, 43200, 86400, 604800, 2592000]
    now = datetime.datetime.now()
    start = now - datetime.timedelta(seconds=(count+1)*cycles[type])
    table = kline_table_list[type]
    logging.debug(start.strftime("%Y-%m-%d %H:%M:%S"))
    missing_position = 0
    data = table.query.filter(table.ex_pair==pair, table.timestamp>=start).\
            order_by(kline_table_list[type].timestamp).all()
    if len(data) == 0:
        data = table.query.filter(table.ex_pair==pair).\
            order_by(kline_table_list[type].block_num.desc()).limit(1).all()
        if len(data) == 1:
            data[0].base_amount = 0
            data[0].quote_amount = 0
    else:
        missing_position = len(data)
    logging.info("missing_position: %d" % missing_position)
    logging.info("timestamp: %s" % data[0].timestamp)
    logging.info("len(data): %d" % len(data))
    if data is None or len(data) == 0:
        return {'data': []}
    last_item = copy.deepcopy(data[len(data)-1])
    last_item.base_amount = 0
    last_item.quote_amount = 0
    last_item.k_open = last_item.k_close
    last_item.k_high = last_item.k_close
    last_item.k_low = last_item.k_close
    while True:
        last_item.timestamp += datetime.timedelta(seconds=cycles[type])
        if last_item.timestamp > now:
            break
    if missing_position == 0:
        data = []
    for i in range(missing_position, count):
        # logging.info(last_item.timestamp)
        last_item.timestamp -= datetime.timedelta(seconds=cycles[type])
        if missing_position > 0 and last_item.timestamp <= data[missing_position-1].timestamp:
            break
        else:
            data.insert(missing_position, copy.deepcopy(last_item))
    return {
            'data': [t.toQueryObj() for t in data]
        }


@jsonrpc.method('hx.fdxqs.exchange.pair.summary()', validate=True)
def hx_fdxqs_exchange_pair_summary():
    data = ContractExchangePair.query.filter_by(stat=1).all()
    pairs = [r.baseAssetSymbol+'/'+r.quoteAssetSymbol for r in data]
    now = datetime.datetime.now()
    last_day = now - datetime.timedelta(days=1)
    summary = []
    for p in pairs:
        logging.info(p)
        data = TxContractDealKdata1Min.query.filter(TxContractDealKdata1Min.ex_pair==p,TxContractDealKdata1Min.timestamp>last_day).order_by(TxContractDealKdata1Min.timestamp.desc()).all()
        if len(data) > 0:
            priceLastDay = data[0].k_close
            priceNow = data[len(data)-1].k_close
            volume = data[len(data)-1].base_amount
            percent = (priceNow - priceLastDay) / priceLastDay
        else:
            data = TxContractDealKdata1Min.query.filter(TxContractDealKdata1Min.ex_pair==p).order_by(TxContractDealKdata1Min.timestamp.desc()).limit(1).first()
            if data is None:
                continue
            priceLastDay = data.k_close
            priceNow = data.k_close
            volume = 0
            percent = 0
        summary.append({'pair': p, 'priceNow': priceNow, 'priceLastDay': priceLastDay, 'volume': volume, 'percent': percent})
    return summary


@app.shell_context_processor
def make_shell_context():
    return dict(app=app, db=db)


@app.cli.command('cleardb')
@click.option('--block', default=0, type=int, help='block number from which to clear')
def cleardb(block):
    #TODO, process order tables rollback.
    table_to_clear = [TxContractRawHistory, BlockRawHistory, TxContractEventHistory, ContractInfo, \
            AccountInfo]
    # ContractPersonExchangeOrder, 
    table_to_clear += kline_table_list
    for t in table_to_clear:
        if block <= 0:
            t.query.delete()
        else:
            logging.info(str(t))
            delete_q = t.__table__.delete().where(t.block_num>=block)
            db.session.execute(delete_q)
    ServiceConfig.query.filter_by(key='scan_block').delete()
    db.session.add(ServiceConfig(key='scan_block', value=str(block-1)))
    db.session.commit()
    print("clear db finished")


@app.cli.command('rpc_test')
@click.argument('method')
@click.argument('args')
def rpc_test(method, args):
    ch = ContractHistory(app.config, db)
    rsp = ch.http_request(method, [args])
    print(str(rsp))


def update_kline_real(times):
    from app.models import TxContractDealKdata5Min, TxContractDealKdata15Min, \
            TxContractDealKdata30Min, TxContractDealKdataDaily, TxContractDealKdata6Hour, \
            TxContractDealKdata1Hour, TxContractDealKdata2Hour, TxContractDealKdata12Hour, \
            TxContractDealKdataMonthly
    def process_kline_common(base_table, target_table, process_obj, pair='HC/HX'):
        logging.debug("base: %s, target: %s, pair: %s" % (str(base_table), str(target_table), pair))
        k_last = target_table.query.filter_by(ex_pair=pair).order_by(target_table.timestamp.desc()).first()
        k = process_obj(k_last)
        if k_last is None:
            # if str(base_table) == "<class 'app.models.TxContractDealTick'>":
            last_time = datetime.datetime.now() - datetime.timedelta(days=365)
        else:
            last_time = k_last.timestamp
        logging.info("last time: %s" % (last_time))
        ticks = base_table.query.filter(base_table.ex_pair==pair, base_table.timestamp>=last_time).order_by(base_table.id).all()
        for t in ticks:
            k.process_tick(t)
        if k_last is not None:
            target_table.query.filter_by(timestamp=k_last.timestamp).delete()
        for r in k.get_k_data():
            db.session.add(target_table(ex_pair=pair, k_open=r['k_open'], k_close=r['k_close'], \
                    k_high=r['k_high'], k_low=r['k_low'], timestamp=r['start_time'], \
                    block_num=r['block_num'], base_amount=r['base_amount'], quote_amount=r['quote_amount']))

    pairs = ContractExchangePair.query.filter_by(stat=1).all()
    for p in pairs:
        ex_pair = p.baseAssetSymbol+"/"+p.quoteAssetSymbol
        # Process 1-minute K-Line
        process_kline_common(TxContractDealTick, TxContractDealKdata1Min, KLine1MinObj, ex_pair)
        # Process 5-minutes K-Line
        process_kline_common(TxContractDealKdata1Min, TxContractDealKdata5Min, KLine5MinObj, ex_pair)
        # Process 15-minutes K-Line
        process_kline_common(TxContractDealKdata1Min, TxContractDealKdata15Min, KLine15MinObj, ex_pair)
        # Process 30-minutes K-Line
        process_kline_common(TxContractDealKdata1Min, TxContractDealKdata30Min, KLine30MinObj, ex_pair)
        # Process 1-hour K-Line
        process_kline_common(TxContractDealKdata1Min, TxContractDealKdata1Hour, KLine1HourObj, ex_pair)
        # Process 2-hour K-Line
        process_kline_common(TxContractDealKdata1Hour, TxContractDealKdata2Hour, KLine2HourObj, ex_pair)
        # Process 6-hour K-Line
        process_kline_common(TxContractDealKdata1Hour, TxContractDealKdata6Hour, KLine6HourObj, ex_pair)
        # Process 12-hour K-Line
        process_kline_common(TxContractDealKdata1Hour, TxContractDealKdata12Hour, KLine12HourObj, ex_pair)
        # Process daily K-Line
        process_kline_common(TxContractDealKdata1Hour, TxContractDealKdataDaily, KLineDailyObj, ex_pair)
        # Process weekly K-Line
        process_kline_common(TxContractDealKdata1Hour, TxContractDealKdataWeekly, KLineWeeklyObj, ex_pair)
        # Process monthly K-Line
        process_kline_common(TxContractDealKdataDaily, TxContractDealKdataMonthly, KLineMonthlyObj, ex_pair)


@app.cli.command('update_kline')
@click.option('--times', default=1, type=int, help='scan times')
def update_kline(times):
    update_kline_real(times)


@app.cli.command('scan_block')
@click.option('--times', default=1, type=int, help='scan times')
@click.option('--kline', default=0, type=int, help='update kline data')
def scan_block(times, kline):
    ch = ContractHistory(app.config, db)
    total = 0
    import time
    while total < times or times <= 0:
        ch.scan_block()
        time.sleep(5)
        total += 1
        if kline == 1:
            update_kline_real(1)
            logging.info("Update kline data finished")
    logging.info("Scan block finished")


@app.cli.command('scan_person_exchange')
def scan_person_exchange():
    ch = ContractHistory(app.config, db)
    ch.exchange_person_orders(1)
    logging.info("scan contract finished")


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
