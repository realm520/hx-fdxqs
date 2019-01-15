# encoding=utf8

import sqlite3
import json
import requests
import logging
# from models import TxRawHistory
from logging.handlers import TimedRotatingFileHandler
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Text


Base = declarative_base()

class TxRawHistory(Base):
    __tablename__ = 'tx_raw_history'
    
    id = Column(Integer, primary_key=True)
    tx_id = Column(String(64), index=True)
    tx_json = Column(Text, default=False)

    def __repr__(self):
        return "<TxRawHistory(id='%s', tx_id='%s', tx_json='%s')>" % (
                   self.id, self.fullname, self.password)


db_source = "hx.s3db"
config_table = "hx_config"
block_table = "hx_block"
user_table = "hx_user"
rpc_connect = "http://132.232.21.36:8099"


def http_request(method, args):
    url = rpc_connect
    args_j = json.dumps(args)
    payload =  "{\r\n \"id\": 1,\r\n \"method\": \"%s\",\r\n \"params\": %s\r\n}" % (method, args_j)
    headers = {
            'content-type': "text/plain",
            'cache-control': "no-cache",
    }
    while True:
        try:
            response = requests.request("POST", url, data=payload, headers=headers)
            #print type(response)
            #print response.text
            rep = response.json()
            if "result" in rep:
                return rep["result"]
        except Exception:
            logging.error("Retry: %s" % payload)
            continue


def get_info_result():
    info = http_request('info', [])
    return info


def scan_block(fromBlock=1, max=0):
    if max > 0:
        maxBlockNum = max
    else:
        info = get_info_result()
        maxBlockNum = int(info['head_block_num'])
    # conn = sqlite3.connect(db_path)
    # c = conn.cursor()
    f = open('hx_contract_txs.csv', 'w+')
    for i in range(fromBlock, maxBlockNum):
        block = http_request('get_block', [i])
        if block is None:
            logging.error("block %d is not fetched" % i)
            continue
        if i % 1000 == 0:
            print("Block height: %d, miner: %s, tx_count: %d" % (block['number'], block['miner'], len(block['transactions'])))
            # conn.commit()
            # f.flush()
        # c.execute("INSERT INTO "+block_table+" VALUES ("+str(block['number'])+",'"+block['miner']+"',"+str(len(block['transactions']))+")")
        if len(block['transactions']) > 0:
            tx_count = 0
            tx_prefix = str(i)+','+block['transaction_ids'][tx_count]
            for t in block['transactions']:
                for op in t['operations']:
                    if op[0] == 76: # contract_register_operation
                        op[1]['contract_code']['code'] = None
                        f.write(tx_prefix+','+str(tx_count)+',contract_register,'+str(op[1])+'\n')
                        logging.info(tx_prefix+','+str(op))
                    elif op[0] == 77: # contract_upgrade_operation
                        f.write(tx_prefix+','+str(tx_count)+',contract_upgrade,'+str(op[1])+'\n')
                        logging.info(tx_prefix+','+str(op))
                    elif op[0] == 78: # native_contract_register_operation
                        f.write(tx_prefix+','+str(tx_count)+',native_contract_register,'+str(op[1])+'\n')
                        logging.info(tx_prefix+','+str(op))
                    elif op[0] == 79: # contract_invoke_operation
                        f.write(tx_prefix+','+str(tx_count)+',contract_invoke_operation,'+str(op[1])+'\n')
                        logging.info(tx_prefix+','+str(op))
                    elif op[0] == 80: # storage_operation
                        f.write(tx_prefix+','+str(tx_count)+',storage_operation,'+str(op[1])+'\n')
                        logging.info(tx_prefix+','+str(op))
                    elif op[0] == 81: # transfer_contract_operation
                        f.write(tx_prefix+','+str(tx_count)+',transfer_contract_operation,'+str(op[1])+'\n')
                        logging.info(tx_prefix+','+str(op))
                    else:
                        logging.info('Not processed: '+str(op[0]))
                        pass
            tx_count += 1
    f.close()
    # conn.commit()
    # conn.close()


if __name__ == '__main__':
    # init log settings
    log_fmt = '%(asctime)s\tFile \"%(filename)s\",line %(lineno)s\t%(levelname)s: %(message)s'
    formatter = logging.Formatter(log_fmt)
    log_file_handler = TimedRotatingFileHandler(filename="hx_util_log", when="D", interval=1, backupCount=7)
    #log_file_handler.suffix = "%Y-%m-%d_%H-%M.log"
    #log_file_handler.extMatch = re.compile(r"^\d{4}-\d{2}-\d{2}_\d{2}-\d{2}.log$")
    log_file_handler.setFormatter(formatter)
    logging.basicConfig(level=logging.INFO)
    log = logging.getLogger()
    log.addHandler(log_file_handler)

    # init database settings
    engine = create_engine('sqlite:///fdxqs.db')


    scan_block(1)
