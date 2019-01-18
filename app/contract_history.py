# encoding=utf8

import sqlite3
import json
import requests
import logging
from app.models import TxContractRawHistory, TxContractDealHistory, ServiceConfig, BlockRawHistory, TxContractEventHistory


class ContractHistory():
    def __init__(self, config, db):
        self.rpc_connect = config['HX_RPC_ENDPOINT']
        self.base_path = config['WORK_DIR']
        self.db = db
        self.block_cache_size = 360
        self.block_cache_limit = 720
        self.block_cache = []

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


    #TODO, fork process
    def check_fork(self, block):
        ret = False
        if len(self.block_cache) == 0:
            self.block_cache = [{'number': block['number'], 'block_id': block['block_id'], 'previous': block['previous']}]
            return ret
        # process fork, rollback to fork block
        for i in range(0, len(self.block_cache)):
            if self.block_cache[i] == block['previous']:
                self.block_cache = [{'number': block['number'], 'block_id': block['block_id'], 'previous': block['previous']}] + self.block_cache[i:]
                ret = True
                break
        # cut size to 360
        if len(self.block_cache) > self.block_cache_limit:
            self.block_cache = self.block_cache[:self.block_cache_size]
        return ret

    def get_contract_invoke_object(self, txid):
        invoke_obj = self.http_request('get_contract_invoke_object', [txid])
        if len(invoke_obj) <= 0:
            return
        self.db.session.add(TxContractEventHistory(tx_id=txid, tx_json=json.dumps(invoke_obj)))
        for obj in invoke_obj:
            if not obj['exec_succeed']:
                continue
            for e in obj['events']:
                if e['event_name'] == 'BuyOrderPutedOn' or e['event_name'] == 'SellOrderPutedOn':
                    order = json.loads(e['event_arg'])
                    for buys in order['transactionBuys']:
                        items = buys.split(',')
                        self.db.session.add(TxContractDealHistory(address=items[2], tx_id=txid, match_tx_id=items[3], base_amount=items[6], \
                                quote_amount=items[7], ex_type='buy', ex_pair=order['exchangPair']))
                    for sells in order['transactionSells']:
                        items = sells.split(',')
                        self.db.session.add(TxContractDealHistory(address=items[2], tx_id=txid, match_tx_id=items[3], base_amount=items[6], \
                                quote_amount=items[7], ex_type='sell', ex_pair=order['exchangPair']))


    def scan_block(self, fromBlock=0, max=0):
        if fromBlock > 0:
            fromBlockNum = fromBlock
        else:
            lastBlockNum = ServiceConfig.query.filter_by(key='scan_block').first()
            if lastBlockNum is None:
                fromBlockNum = 1
            else:
                fromBlockNum = int(lastBlockNum.value) + 1
        if max > 0:
            maxBlockNum = max
        else:
            info = self.get_info_result()
            maxBlockNum = int(info['head_block_num'])
        for i in range(fromBlockNum, maxBlockNum):
            block = self.http_request('get_block', [i])
            if block is None:
                logging.error("block %d is not fetched" % i)
                continue
            # self.check_fork(block)
            self.db.session.add(BlockRawHistory(block_height=block['number'], block_id=block['block_id'], prev_id=block['previous'], \
                    timestamp=block['timestamp'], trxfee=block['trxfee'], miner=block['miner'], next_secret_hash=block['next_secret_hash'], \
                    previous_secret=block['previous_secret'], reward=block['reward'], signing_key=block['signing_key']))
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
                        is_contract_type = True
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
                                    op_seq=op_count, tx_type='transfer_contract_operation', tx_json=json.dumps(op[1])))
                            logging.debug(tx_prefix+','+str(op))
                        else:
                            is_contract_type = False
                            logging.debug('Not processed: '+json.dumps(op[0]))
                    if is_contract_type:
                        self.get_contract_invoke_object(block['transaction_ids'][tx_count])
                        op_count += 1
                    tx_count += 1
        ServiceConfig.query.filter_by(key='scan_block').delete()
        self.db.session.add(ServiceConfig(key='scan_block', value=str(maxBlockNum-1)))
        self.db.session.commit()

