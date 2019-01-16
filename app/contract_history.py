# encoding=utf8

import sqlite3
import json
import requests
import logging
from app.models import TxContractRawHistory, TxContractDealHistory, ServiceConfig


class ContractHistory():
    def __init__(self, config, db):
        self.rpc_connect = config['HX_RPC_ENDPOINT']
        self.base_path = config['WORK_DIR']
        self.db = db

    def http_request(self, method, args):
        args_j = json.dumps(args)
        payload =  "{\r\n \"id\": 1,\r\n \"method\": \"%s\",\r\n \"params\": %s\r\n}" % (method, args_j)
        headers = {
                'content-type': "text/plain",
                'cache-control': "no-cache",
        }
        while True:
            try:
                response = requests.request("POST", self.rpc_connect, data=payload, headers=headers)
                #print type(response)
                #print response.text
                rep = response.json()
                if "result" in rep:
                    return rep["result"]
            except Exception:
                logging.error("Retry: %s" % payload)
                continue
    

    def get_info_result(self):
        info = self.http_request('info', [])
        return info


    def scan_block(self, fromBlock=1, max=0):
        if max > 0:
            maxBlockNum = max
        else:
            info = self.get_info_result()
            maxBlockNum = int(info['head_block_num'])
        # conn = sqlite3.connect(db_path)
        # c = conn.cursor()
        f = open(self.base_path+'/hx_contract_txs.csv', 'a')
        for i in range(fromBlock, maxBlockNum):
            block = self.http_request('get_block', [i])
            if block is None:
                logging.error("block %d is not fetched" % i)
                continue
            if i % 1000 == 0:
                logging.info("Block height: %d, miner: %s, tx_count: %d" % (block['number'], block['miner'], len(block['transactions'])))
                ServiceConfig.query.filter_by(key='scan_block').delete()
                self.db.session.add(ServiceConfig(key='scan_block', value=str(i)))
                self.db.session.commit()
            if len(block['transactions']) > 0:
                tx_count = 0
                tx_prefix = str(i)+'|'+block['transaction_ids'][tx_count]
                for t in block['transactions']:
                    op_count = 0
                    for op in t['operations']:
                        tx = None
                        if op[0] == 76: # contract_register_operation
                            op[1]['contract_code']['code'] = None
                            self.db.session.add(TxContractRawHistory(block_height=i, tx_id=block['transaction_ids'][tx_count], \
                                    op_seq=op_count, tx_type='contract_register', tx_json=json.dumps(op[1])))
                            logging.debug(tx_prefix+','+str(op))
                        elif op[0] == 77: # contract_upgrade_operation
                            self.db.session.add(TxContractRawHistory(block_height=i, tx_id=block['transaction_ids'][tx_count], \
                                    op_seq=op_count, tx_type='contract_upgrade', tx_json=json.dumps(op[1])))
                            logging.debug(tx_prefix+','+str(op))
                        elif op[0] == 78: # native_contract_register_operation
                            self.db.session.add(TxContractRawHistory(block_height=i, tx_id=block['transaction_ids'][tx_count], \
                                    op_seq=op_count, tx_type='native_contract_register', tx_json=json.dumps(op[1])))
                            logging.debug(tx_prefix+','+str(op))
                        elif op[0] == 79: # contract_invoke_operation
                            self.db.session.add(TxContractRawHistory(block_height=i, tx_id=block['transaction_ids'][tx_count], \
                                    op_seq=op_count, tx_type='contract_invoke_operation', tx_json=json.dumps(op[1])))
                            logging.debug(tx_prefix+','+str(op))
                        elif op[0] == 80: # storage_operation
                            self.db.session.add(TxContractRawHistory(block_height=i, tx_id=block['transaction_ids'][tx_count], \
                                    op_seq=op_count, tx_type='contract_invoke_operation', tx_json=json.dumps(op[1])))
                            logging.debug(tx_prefix+','+str(op))
                        elif op[0] == 81: # transfer_contract_operation
                            self.db.session.add(TxContractRawHistory(block_height=i, tx_id=block['transaction_ids'][tx_count], \
                                    op_seq=tx_count, tx_type='transfer_contract_operation', tx_json=json.dumps(op[1])))
                            logging.debug(tx_prefix+','+str(op))
                        else:
                            logging.debug('Not processed: '+json.dumps(op[0]))
                        op_count += 1
                    tx_count += 1
        ServiceConfig.query.filter_by(key='scan_block').delete()
        self.db.session.add(ServiceConfig(key='scan_block', value=str(maxBlockNum-1)))
        self.db.session.commit()

