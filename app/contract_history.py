# encoding=utf8

import sqlite3
import json
import requests
import logging
from app.models import TxContractRawHistory, TxContractDealHistory, ContractInfo, \
        ServiceConfig, BlockRawHistory, TxContractEventHistory, ContractPersonExchangeEvent, \
        ContractPersonExchangeOrder, TxContractDealKdataDaily, TxContractDealKdataHourly, \
        TxContractDealKdataWeekly
from sqlalchemy import func


class ContractHistory():
    OP_TYPE_CONTRACT_REGISTER = 76
    OP_TYPE_CONTRACT_UPGRADE = 77
    OP_TYPE_CONTRACT_INVOKE = 79
    EXCHANGE_PERSON_TYPE_ABI = r'["cancelAllOrder", "cancelSellOrder", "cancelSellOrderPair", "close", "init", "on_deposit_asset", "on_destroy", "putOnSellOrder", "withdrawAll", "withdrawAsset", "withrawRemainAsset"]'
    EXCHANGE_PAIR_TYPE_ABI = r'["cancelBuyOrder", "cancelSellOrder", "init", "init_config", "on_deposit_asset", "on_destroy", "putOnBuyOrder", "putOnSellOrder", "reorganizeSlots", "testtable"]'
    EXCHANGE_TYPE_ABI = r'["cancelChangeAdminProposal", "cancelOrder", "cancelRegisterExchangePairProposal", "cancelUnboundExchangePairProposal", "freezeExchangePair", "init", "init_config", "on_deposit_asset", "on_destroy", "putOnBuyOrder", "putOnSellOrder", "reorganizeSlots", "submitChangeAdminProposal", "submitRegisterExchangePairProposal", "submitUnboundExchangePairProposal", "unfreezeExchangePair", "unlockUserOffPairBalance", "voteChangeAdminProposal", "voteRegisterExchangePairProposal", "voteUnboundExchangePairProposal", "withdraw"]'
    STO_TYPE_ABI = r'["addCrowdfundingInfo", "adminWithdrawFund", "approve", "changeAdmin", "closeCrowdfunding", "deleteLastCrowdfundingInfo", "init", "init_config", "modifyLastCrowdfundingInfo", "on_deposit_asset", "on_destroy", "openCrowdfunding", "pause", "resume", "returnAllCrowdAssetBack", "stop", "transfer", "transferFrom", "userGetCrowdAssetBack", "withdrawBonuses"]'


    def __init__(self, config, db):
        self.rpc_connect = config['HX_RPC_ENDPOINT']
        self.base_path = config['WORK_DIR']
        self.db = db
        self.contract_caller = config['CONTRACT_CALLER']
        self.block_cache_size = 360
        self.block_cache_limit = 720
        self.load_block_cache()


    def load_block_cache(self):
        cache_records = BlockRawHistory.query.order_by(BlockRawHistory.block_num.desc()).limit(self.block_cache_size).all()
        self.block_cache = []
        for record in cache_records:
            self.block_cache.append({'number': record.block_num, 'block_id': record.block_id, 'previous': record.prev_id})
        logging.info('Load %d records to block_cache.' % len(cache_records))
        if len(self.block_cache) > 0:
            logging.info('Latest block height: %d .' % self.block_cache[0]['number'])


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


    def clear_dirty_data(self, block_num):
        TxContractRawHistory.query.filter(TxContractRawHistory.block_num>=block_num).delete()
        TxContractEventHistory.query.filter(TxContractEventHistory.block_num>=block_num).delete()
        ContractInfo.query.filter(ContractInfo.block_num>=block_num).delete()
        TxContractDealHistory.query.filter(TxContractDealHistory.block_num>=block_num).delete()
        ContractPersonExchangeEvent.query.filter(ContractPersonExchangeEvent.block_num>=block_num).delete()
        BlockRawHistory.query.filter(BlockRawHistory.block_num>=block_num).delete()
        TxContractDealKdataHourly.query.filter(TxContractDealKdataHourly.block_num>=block_num).delete()
        TxContractDealKdataDaily.query.filter(TxContractDealKdataDaily.block_num>=block_num).delete()
        TxContractDealKdataWeekly.query.filter(TxContractDealKdataWeekly.block_num>=block_num).delete()


    #TODO, fork process
    def check_fork(self, block):
        if len(self.block_cache) == 0:
            self.block_cache = [{'number': block['number'], 'block_id': block['block_id'], 'previous': block['previous']}]
            return False
        # process fork, rollback to fork block
        if self.block_cache[0]['block_id'] == block['previous'] and self.block_cache[0]['number'] == block['number']-1:
            self.block_cache = [{'number': block['number'], 'block_id': block['block_id'], 'previous': block['previous']}] + self.block_cache
        else:
            rollback_block_num = 0
            for i in range(0, len(self.block_cache)):
                block = self.http_request('get_block', [self.block_cache[i]['number']])
                if block['block_id'] == self.block_cache[i]['block_id']:
                    rollback_block_num = block['number']
                    break
            if rollback_block_num > 0:
                logging.warn('Fork from %d, set back block number and return [True].' % rollback_block_num)
                ServiceConfig.query.filter_by(key='scan_block').delete()
                self.db.session.add(ServiceConfig(key='scan_block', value=str(rollback_block_num)))
                self.db.session.commit()
                return True
        # cut size to 360
        if len(self.block_cache) > self.block_cache_limit:
            self.block_cache = self.block_cache[:self.block_cache_size]
        return False


    def exchange_person_orders(self, block_num):
        updated_contracts = ContractPersonExchangeEvent.query.filter(ContractPersonExchangeEvent.block_num>=block_num).all()
        for contract in updated_contracts:
            ret = self.http_request("invoke_contract_offline",
                    [self.contract_caller, contract.contract_address, "sell_orders", ""])
            result = json.loads(ret)
            if isinstance(result, dict):
                ContractPersonExchangeOrder.query.filter_by(contract_address=contract.contract_address).delete()
                for k, v in result.items():
                    [from_asset, to_asset] = k.split(',')
                    order_info = json.loads(v)
                    for o in order_info['orderArray']:
                        [from_supply, to_supply, price] = o.split(',')
                        self.db.session.add(ContractPersonExchangeOrder(from_asset=from_asset, to_asset=to_asset, \
                                from_supply=from_supply, to_supply=to_supply, price=price, \
                                contract_address=contract.contract_address))
        self.db.session.commit()


    def get_contract_invoke_object(self, op, txid, block):
        invoke_obj = self.http_request('get_contract_invoke_object', [txid])
        if len(invoke_obj) <= 0:
            return
        self.db.session.add(TxContractEventHistory(tx_id=txid, tx_json=json.dumps(invoke_obj), block_num=block['number']))
        for obj in invoke_obj:
            if not obj['exec_succeed']:
                continue
            if op[0] == ContractHistory.OP_TYPE_CONTRACT_REGISTER:
                abi = json.dumps(op[1]['contract_code']['abi'])
                if abi == ContractHistory.STO_TYPE_ABI:
                    contract_type = 'sto'
                elif abi == ContractHistory.EXCHANGE_PAIR_TYPE_ABI:
                    contract_type = 'exchange_pair'
                elif abi == ContractHistory.EXCHANGE_PERSON_TYPE_ABI:
                    contract_type = 'exchange_personal'
                elif abi == ContractHistory.EXCHANGE_TYPE_ABI:
                    contract_type = 'exchange'
                else:
                    contract_type = 'unknown'
                self.db.session.add(ContractInfo(invoker=obj['invoker'], contract_id=obj['contract_registed'], \
                        tx_id=txid, abi=abi, code_hash=op[1]['contract_code']['code_hash'], \
                        offline_abi=json.dumps(op[1]['contract_code']['offline_abi']), block_num=block['number'], \
                        timestamp=block['timestamp'], contract_type=contract_type))
            elif op[0] == ContractHistory.OP_TYPE_CONTRACT_INVOKE:
                contract_info = ContractInfo.query.filter_by(contract_id=op[1]['contract_id']).first()
                if contract_info is None:
                    continue
                contract_type = contract_info.contract_type
                for e in obj['events']:
                    if contract_type == 'exchange' and (e['event_name'] == 'BuyOrderPutedOn' or e['event_name'] == 'SellOrderPutedOn'):
                        order = json.loads(e['event_arg'])
                        for buys in order['transactionBuys']:
                            items = buys.split(',')
                            self.db.session.add(TxContractDealHistory(address=items[2], tx_id=txid, match_tx_id=items[3], base_amount=int(items[6]), \
                                    quote_amount=int(items[7]), ex_type='buy', ex_pair=order['exchangPair'], block_num=int(block['number']), \
                                    timestamp=block['timestamp']))
                        for sells in order['transactionSells']:
                            items = sells.split(',')
                            self.db.session.add(TxContractDealHistory(address=items[2], tx_id=txid, match_tx_id=items[3], base_amount=int(items[6]), \
                                    quote_amount=int(items[7]), ex_type='sell', ex_pair=order['exchangPair'], block_num=int(block['number']), \
                                    timestamp=block['timestamp']))
                    elif contract_type == 'exchange_personal':
                        self.db.session.add(ContractPersonExchangeEvent(caller_addr=e['caller_addr'], event_name=e['event_name'], \
                                event_arg=e['event_arg'], block_num=int(e['block_num']), op_num=int(e['op_num']), contract_address=e['contract_address'], \
                                timestamp=block['timestamp'], tx_id=txid))


    def process_kline_data(self, fromBlock):
        block_num = fromBlock - fromBlock % 720
        data = TxContractDealHistory.query().\
                filter(TxContractDealHistory.block_num>=block_num).order_by(TxContractDealHistory.block_num).all()
        k_open = None
        k_low = None
        k_high = None
        for d in data:
            price = d.base_amount / d.quote_amount
            if k_open is None:
                k_open = price
                block_open = d.block_num
                timestamp = d.timestamp
            if k_low is None or k_low > price:
                k_low = price
            if k_high is None or k_high < price:
                k_high = price
            if d.block_num % 720 == 719:
                self.db.session.add(TxContractDealKdataHourly(k_open=k_open, k_close=price, \
                        k_high=k_high, k_low=k_low, block_num=block_open, timestamp=timestamp))
                k_open = None
                k_low = None
                k_high = None


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
        self.clear_dirty_data(fromBlockNum)
        lastBlockNumBeforeCommit = fromBlockNum
        for i in range(fromBlockNum, maxBlockNum):
            block = self.http_request('get_block', [i])
            if block is None:
                logging.error("block %d is not fetched" % i)
                continue
            if self.check_fork(block):
                return
            self.db.session.add(BlockRawHistory(block_num=block['number'], block_id=block['block_id'], prev_id=block['previous'], \
                    timestamp=block['timestamp'], trxfee=block['trxfee'], miner=block['miner'], next_secret_hash=block['next_secret_hash'], \
                    previous_secret=block['previous_secret'], reward=block['reward'], signing_key=block['signing_key']))
            if len(block['transactions']) > 0:
                tx_count = 0
                tx_prefix = str(i)+'|'+block['transaction_ids'][tx_count]
                for t in block['transactions']:
                    op_count = 0
                    for op in t['operations']:
                        is_contract_type = True
                        if op[0] == ContractHistory.OP_TYPE_CONTRACT_REGISTER:
                            op[1]['contract_code']['code'] = None
                            self.db.session.add(TxContractRawHistory(block_num=i, tx_id=block['transaction_ids'][tx_count], \
                                    op_seq=op_count, tx_type='contract_register', tx_json=json.dumps(op[1])))
                            logging.debug(tx_prefix+','+str(op))
                        elif op[0] == ContractHistory.OP_TYPE_CONTRACT_UPGRADE:
                            self.db.session.add(TxContractRawHistory(block_num=i, tx_id=block['transaction_ids'][tx_count], \
                                    op_seq=op_count, tx_type='contract_upgrade', tx_json=json.dumps(op[1])))
                            logging.debug(tx_prefix+','+str(op))
                        elif op[0] == 78: # native_contract_register_operation
                            self.db.session.add(TxContractRawHistory(block_num=i, tx_id=block['transaction_ids'][tx_count], \
                                    op_seq=op_count, tx_type='native_contract_register', tx_json=json.dumps(op[1])))
                            logging.debug(tx_prefix+','+str(op))
                        elif op[0] == ContractHistory.OP_TYPE_CONTRACT_INVOKE:
                            self.db.session.add(TxContractRawHistory(block_num=i, tx_id=block['transaction_ids'][tx_count], \
                                    op_seq=op_count, tx_type='contract_invoke_operation', tx_json=json.dumps(op[1])))
                            logging.debug(tx_prefix+','+str(op))
                        elif op[0] == 80: # storage_operation
                            self.db.session.add(TxContractRawHistory(block_num=i, tx_id=block['transaction_ids'][tx_count], \
                                    op_seq=op_count, tx_type='storage_operation', tx_json=json.dumps(op[1])))
                            logging.debug(tx_prefix+','+str(op))
                        elif op[0] == 81: # transfer_contract_operation
                            self.db.session.add(TxContractRawHistory(block_num=i, tx_id=block['transaction_ids'][tx_count], \
                                    op_seq=op_count, tx_type='transfer_contract_operation', tx_json=json.dumps(op[1])))
                            logging.debug(tx_prefix+','+str(op))
                        else:
                            is_contract_type = False
                            logging.debug('Not processed: '+json.dumps(op[0]))
                    if is_contract_type:
                        self.get_contract_invoke_object(op, block['transaction_ids'][tx_count], block)
                        op_count += 1
                    tx_count += 1
            if i % 1024 == 0:
                logging.info("Block height: %d, miner: %s, tx_count: %d" % (block['number'], block['miner'], len(block['transactions'])))
                self.exchange_person_orders(lastBlockNumBeforeCommit)
                ServiceConfig.query.filter_by(key='scan_block').delete()
                self.db.session.add(ServiceConfig(key='scan_block', value=str(i)))
                self.db.session.commit()
                lastBlockNumBeforeCommit = i
        ServiceConfig.query.filter_by(key='scan_block').delete()
        self.db.session.add(ServiceConfig(key='scan_block', value=str(maxBlockNum-1)))
        self.db.session.commit()
        logging.info("Scan block from %d to %d complete." % (fromBlockNum, maxBlockNum))

