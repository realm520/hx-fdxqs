# encoding=utf8

import sqlite3
import json
import requests
import logging
import datetime
from app.models import TxContractRawHistory, ContractInfo, \
        ServiceConfig, BlockRawHistory, TxContractEventHistory, ContractPersonExchangeEvent, \
        ContractPersonExchangeOrder, AccountInfo, CrossChainAssetInOut, TxContractDealTick, \
        kline_table_list, ContractExchangeOrder, TxContractDepositWithdraw
from sqlalchemy import func


class ContractHistory():
    OP_TYPE_REGISTER_ACCOUNT = 5
    OP_TYPE_CROSSCHAIN_DEPOSIT = 60
    OP_TYPE_CROSSCHAIN_WITHDRAW = 61
    OP_TYPE_CROSSCHAIN_WITHDRAW_SIGN = 62
    OP_TYPE_CROSSCHAIN_WITHDRAW_COMBINE = 64
    OP_TYPE_CROSSCHAIN_WITHDRAW_RESULT = 65
    # OP_TYPE_CROSSCHAIN_WITHDRAW_COMBINE_ETH = 98
    OP_TYPE_CONTRACT_REGISTER = 76
    OP_TYPE_CONTRACT_UPGRADE = 77
    OP_TYPE_CONTRACT_INVOKE = 79
    OP_TYPE_CONTRACT_TRANSFER = 81
    EXCHANGE_PERSON_TYPE_ABI = r'["cancelAllOrder", "cancelSellOrder", "cancelSellOrderPair", "close", "init", "on_deposit_asset", "on_destroy", "putOnSellOrder", "withdrawAll", "withdrawAsset", "withrawRemainAsset"]'
    EXCHANGE_PAIR_TYPE_ABI = r'["buySlot", "buySlotsInfo", "buy_orders_num", "getBuyOrders", "getInfo", "getSellOrders", "getUserBuyOrders", "getUserBuyOrdersCount", "getUserSellOrders", "getUserSellOrdersCount", "sellSlot", "sellSlotsInfo", "sell_orders_num"]'
    STO_TYPE_ABI = r'["addCrowdfundingInfo", "adminWithdrawFund", "approve", "changeAdmin", "closeCrowdfunding", "deleteLastCrowdfundingInfo", "init", "init_config", "modifyLastCrowdfundingInfo", "on_deposit_asset", "on_destroy", "openCrowdfunding", "pause", "resume", "returnAllCrowdAssetBack", "stop", "transfer", "transferFrom", "userGetCrowdAssetBack", "withdrawBonuses"]'


    def __init__(self, config, db):
        self.rpc_connect = config['HX_RPC_ENDPOINT']
        self.base_path = config['WORK_DIR']
        self.db = db
        self.contract_exchange_id = config['CONTRACT_EXCHANGE_ID']
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
                logging.debug("[HTTP POST] %s" % payload)
                response = requests.request("POST", self.rpc_connect, data=payload, headers=headers)
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
        # TxContractDealHistory.query.filter(TxContractDealHistory.block_num>=block_num).delete()
        ContractPersonExchangeEvent.query.filter(ContractPersonExchangeEvent.block_num>=block_num).delete()
        BlockRawHistory.query.filter(BlockRawHistory.block_num>=block_num).delete()
        for t in kline_table_list:
            t.query.filter(t.block_num>=block_num).delete()


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
                elif obj['contract_registed'] in self.contract_exchange_id:
                    contract_type = 'exchange'
                else:
                    contract_type = 'unknown'
                self.db.session.add(ContractInfo(invoker=obj['invoker'], contract_id=obj['contract_registed'], \
                        tx_id=txid, abi=abi, code_hash=op[1]['contract_code']['code_hash'], \
                        offline_abi=json.dumps(op[1]['contract_code']['offline_abi']), block_num=block['number'], \
                        timestamp=block['timestamp'], contract_type=contract_type))
            elif op[0] == ContractHistory.OP_TYPE_CONTRACT_TRANSFER:
                contract_info = ContractInfo.query.filter_by(contract_id=op[1]['contract_id']).first()
                if contract_info is None:
                    continue
                contract_type = contract_info.contract_type
                for e in obj['events']:
                    if contract_type == 'exchange' and e['event_name'] == 'Deposited':
                        order = json.loads(e['event_arg'])
                        self.db.session.add(TxContractDepositWithdraw(tx_id=txid, address=order['from_address'], \
                                timestamp=block['timestamp'], block_num=int(block['number']), amount=order['amount'], \
                                asset_type='deposit', asset_symbol=order['symbol'], fee=0))
            elif op[0] == ContractHistory.OP_TYPE_CONTRACT_INVOKE:
                contract_info = ContractInfo.query.filter_by(contract_id=op[1]['contract_id']).first()
                if contract_info is None:
                    continue
                contract_type = contract_info.contract_type
                for e in obj['events']:
                    if contract_type == 'exchange' and e['event_name'] == 'Withdrawed':
                        order = json.loads(e['event_arg'])
                        self.db.session.add(TxContractDepositWithdraw(tx_id=txid, address=order['to_address'], \
                                timestamp=block['timestamp'], block_num=int(block['number']), amount=order['amount'], \
                                asset_type='withdraw', asset_symbol=order['symbol'], fee=order['fee']))
                    elif contract_type == 'exchange' and (e['event_name'] == 'BuyOrderPutedOn' or e['event_name'] == 'SellOrderPutedOn'):
                        order = json.loads(e['event_arg'])
                        items = order['putOnOrder'].split(',')
                        self.db.session.add(ContractExchangeOrder(address=items[2], tx_id=txid, origin_base_amount=int(items[0]), \
                            origin_quote_amount=int(items[1]), ex_type=order['OrderType'], ex_pair=order['exchangPair'], \
                            block_num=int(block['number']), current_base_amount=int(items[0]), current_quote_amount=int(items[1]), \
                            timestamp=block['timestamp'], stat=1))
                        for buys in order['transactionBuys']:
                            items = buys.split(',')
                            maker_tx = ContractExchangeOrder.query.filter_by(tx_id=items[3]).first()
                            if maker_tx is None:
                                logging.error('Matched txid is not found: %s' % items[3])
                            else:
                                maker_tx.current_base_amount = int(items[0])
                                maker_tx.current_quote_amount = int(items[1])
                                if int(items[0]) <= 0 or int(items[1]) <= 0:
                                    maker_tx.stat = 3
                                else:
                                    maker_tx.stat = 2
                                self.db.session.add(maker_tx)
                        for sells in order['transactionSells']:
                            items = sells.split(',')
                            maker_tx = ContractExchangeOrder.query.filter_by(tx_id=items[3]).first()
                            if maker_tx is None:
                                logging.error('Matched txid is not found: %s' % items[3])
                            else:
                                maker_tx.current_base_amount = int(items[0])
                                maker_tx.current_quote_amount = int(items[1])
                                if int(items[0]) <= 0 or int(items[1]) <= 0:
                                    maker_tx.stat = 3
                                else:
                                    maker_tx.stat = 2
                                self.db.session.add(maker_tx)
                        if order['totalExchangeBaseAmount'] > 0:
                            self.db.session.add(TxContractDealTick(tx_id=txid, base_amount=int(order['totalExchangeBaseAmount']), \
                                    quote_amount=int(order['totalExchangeQuoteAmount']), ex_pair=order['exchangPair'], block_num=int(block['number']), \
                                    timestamp=block['timestamp']))
                    elif contract_type == 'exchange' and (e['event_name'] == 'OrderCanceled'):
                        order = json.loads(e['event_arg'])
                        maker_tx = ContractExchangeOrder.query.filter_by(tx_id=order['txid']).first()
                        if maker_tx is None:
                            logging.error('Matched txid is not found: %s' % order['txid'])
                        else:
                            maker_tx.stat = 4
                            self.db.session.add(maker_tx)
                    elif contract_type == 'exchange_personal':
                        self.db.session.add(ContractPersonExchangeEvent(caller_addr=e['caller_addr'], event_name=e['event_name'], \
                                event_arg=e['event_arg'], block_num=int(e['block_num']), op_num=int(e['op_num']), contract_address=e['contract_address'], \
                                timestamp=block['timestamp'], tx_id=txid))


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
        logging.info("Scan block from [%d] to [%d]" % (fromBlockNum, maxBlockNum))
        for i in range(fromBlockNum, maxBlockNum):
            block = self.http_request('get_block', [i])
            if block is None:
                logging.error("block %d is not fetched" % i)
                continue
            if self.check_fork(block):
                return
            block['timestamp'] = datetime.datetime.strptime(block['timestamp'], r"%Y-%m-%dT%H:%M:%S")
            self.db.session.add(BlockRawHistory(block_num=block['number'], block_id=block['block_id'], prev_id=block['previous'], \
                    timestamp=block['timestamp'], trxfee=block['trxfee'], miner=block['miner'], next_secret_hash=block['next_secret_hash'], \
                    previous_secret=block['previous_secret'], reward=block['reward'], signing_key=block['signing_key']))
            if len(block['transactions']) > 0:
                tx_count = 0
                tx_prefix = str(i)+'|'+block['transaction_ids'][tx_count]
                for t in block['transactions']:
                    # print(tx_prefix)
                    op_count = 0
                    for op in t['operations']:
                        logging.debug(tx_prefix+','+str(op))
                        if op[0] == ContractHistory.OP_TYPE_CONTRACT_REGISTER or op[0] == ContractHistory.OP_TYPE_CONTRACT_UPGRADE \
                                or op[0] == 78 or op[0] == ContractHistory.OP_TYPE_CONTRACT_INVOKE or op[0] == 80 \
                                or op[0] == ContractHistory.OP_TYPE_CONTRACT_TRANSFER:
                            if op[1].has_key('contract_code'):
                                op[1]['contract_code']['code'] = None
                            self.db.session.add(TxContractRawHistory(block_num=i, tx_id=block['transaction_ids'][tx_count], \
                                    op_seq=op_count, op_type=op[0], tx_json=json.dumps(op[1])))
                            self.get_contract_invoke_object(op, block['transaction_ids'][tx_count], block)
                        elif op[0] == ContractHistory.OP_TYPE_REGISTER_ACCOUNT:
                            self.db.session.add(AccountInfo(block_num=i, tx_id=block['transaction_ids'][tx_count], \
                                    name=op[1]['name'], address=op[1]['payer'], amount=float(op[1]['fee']['amount']), \
                                    user_id=t['operation_results'][0][1], timestamp=block['timestamp']))
                        elif op[0] == ContractHistory.OP_TYPE_CROSSCHAIN_DEPOSIT:
                            self.db.session.add(CrossChainAssetInOut(block_num=i, tx_id=block['transaction_ids'][tx_count], \
                                    cross_chain_tx_id=op[1]['cross_chain_trx']['trx_id'], \
                                    cross_chain_from=op[1]['cross_chain_trx']['from_account'], \
                                    cross_chain_to=op[1]['cross_chain_trx']['to_account'], \
                                    cross_chain_block_num=int(op[1]['cross_chain_trx']['block_num']), \
                                    amount=float(op[1]['cross_chain_trx']['amount']), asset_symbol=op[1]['asset_symbol'], \
                                    asset_id=op[1]['asset_id'], hx_address=op[1]['deposit_address'], \
                                    timestamp=block['timestamp']))
                            '''
                            # record tx_id of op_61, check tx_id of op_62.ccw_trx_ids, check tx_id of op_64.crosschain_trx_id(ETH is different, combined with contract_id and msg_prefix), check tx_id of op_65.['cross_chain_trx']['trx_id']
                            elif op[0] == ContractHistory.OP_TYPE_CROSSCHAIN_WITHDRAW:
                                print('61'+block['transaction_ids'][tx_count])
                                self.db.session.add(CrossChainAssetInOut(block_num=i, tx_id=block['transaction_ids'][tx_count], \
                                        cross_chain_to=op[1]['crosschain_account'], asset_symbol=op[1]['asset_symbol'], \
                                        asset_id=op[1]['asset_id'], hx_address=op[1]['withdraw_account'], \
                                        timestamp=block['timestamp']))
                            elif op[0] == ContractHistory.OP_TYPE_CROSSCHAIN_WITHDRAW_SIGN:
                                for wid in op[1]['ccw_trx_ids']:
                                    print('62'+block['transaction_ids'][tx_count]+'|'+wid)
                                    withdraw_record = CrossChainAssetInOut.query.filter_by(tx_id=wid).first()
                                    if withdraw_record is None:
                                        logging.error('Not found withdraw tx id: %s' % wid)
                                        continue
                                    withdraw_record.sign_tx_id = block['transaction_ids'][tx_count]
                                    self.db.session.add(withdraw_record)
                            elif op[0] == ContractHistory.OP_TYPE_CROSSCHAIN_WITHDRAW_COMBINE:
                                print('64'+block['transaction_ids'][tx_count]+'|'+op[1]['withdraw_trx'])
                                withdraw_record = CrossChainAssetInOut.query.filter_by(sign_tx_id=op[1]['withdraw_trx']).first()
                                if withdraw_record.asset_symbol == 'ETH' or withdraw_record.asset_symbol.find('ERC') == 0:
                                    withdraw_record.cross_chain_tx_id = op[1]['crosschain_trx_id']['source_trx']['contract_addr']\
                                            +'|'+op[1]['crosschain_trx_id']['source_trx']['msg_prefix']
                                else:
                                    withdraw_record.cross_chain_tx_id = op[1]['crosschain_trx_id']
                                withdraw_record.combine_tx_id = block['transaction_ids'][tx_count]
                                self.db.session.add(withdraw_record)
                            elif op[0] == ContractHistory.OP_TYPE_CROSSCHAIN_WITHDRAW_RESULT:
                                asset_symbol = op[1]['cross_chain_trx']['asset_symbol']
                                combine_trx_id = op[1]['cross_chain_trx']['trx_id']
                                if asset_symbol == 'ETH' or asset_symbol.find('ERC') == 0:
                                    combine_trx_id = combine_trx_id[combine_trx_id.find('|')+1:]
                                withdraw_record = CrossChainAssetInOut.query.\
                                        filter_by(cross_chain_tx_id=combine_trx_id).first()
                                withdraw_record.cross_chain_from = op[1]['cross_chain_trx']['from_account']
                                withdraw_record.cross_chain_block_num = op[1]['cross_chain_trx']['block_num']
                                withdraw_record.amount = -1 * float(op[1]['cross_chain_trx']['amount'])
                                self.db.session.add(withdraw_record)
                            '''
                        else:
                            logging.debug('Not processed: '+json.dumps(op[0]))
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

