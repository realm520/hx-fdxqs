from . import db



class ServiceConfig(db.Model):
    __tablename__ = 'service_config'
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(64), unique=True, index=True)
    value = db.Column(db.Text, default=False)

    def __init__(self, **kwargs):
        super(ServiceConfig, self).__init__(**kwargs)

    def __repr__(self):
        return '<ServiceConfig %r>' % self.key



class TxContractRawHistory(db.Model):
    __tablename__ = 'tx_contract_raw_history'
    id = db.Column(db.Integer, primary_key=True)
    block_num = db.Column(db.Integer)
    tx_id = db.Column(db.String(64), index=True)
    op_seq = db.Column(db.Integer)
    op_type = db.Column(db.Integer)
    tx_json = db.Column(db.Text)

    def __init__(self, **kwargs):
        super(TxContractRawHistory, self).__init__(**kwargs)

    def __repr__(self):
        return '<TxContractRawHistory %r>' % self.tx_id


class TxContractEventHistory(db.Model):
    __tablename__ = 'tx_contract_event_history'
    id = db.Column(db.Integer, primary_key=True)
    tx_id = db.Column(db.String(64), index=True)
    tx_json = db.Column(db.Text)
    block_num = db.Column(db.Integer)

    def __init__(self, **kwargs):
        super(TxContractEventHistory, self).__init__(**kwargs)

    def __repr__(self):
        return '<TxContractEventHistory %r>' % self.tx_id


class AccountInfo(db.Model):
    __tablename__ = 'account_info'
    id = db.Column(db.Integer, primary_key=True)
    tx_id = db.Column(db.String(64))
    name = db.Column(db.String(64), index=True)
    user_id = db.Column(db.String(64), index=True)
    address = db.Column(db.String(64), index=True)
    amount = db.Column(db.BigInteger)
    block_num = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime)

    def __init__(self, **kwargs):
        super(AccountInfo, self).__init__(**kwargs)

    def __repr__(self):
        return '<AccountInfo %r>' % self.tx_id
    
    def toQueryObj(self):
        return {"tx_id": self.tx_id, "name": self.name, "address": self.address, "user_id": self.user_id, \
                "amount": self.amount, "block_num": self.block_num, "timestamp": self.timestamp}


class ContractInfo(db.Model):
    __tablename__ = 'contract_info'
    id = db.Column(db.Integer, primary_key=True)
    invoker = db.Column(db.String(64), index=True)
    contract_id = db.Column(db.String(64), index=True)
    tx_id = db.Column(db.String(64))
    abi = db.Column(db.Text)
    offline_abi = db.Column(db.Text)
    code_hash = db.Column(db.String(64))
    contract_type = db.Column(db.String(64))
    block_num = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime)

    def __init__(self, **kwargs):
        super(ContractInfo, self).__init__(**kwargs)

    def __repr__(self):
        return '<ContractInfo %r>' % self.tx_id
    
    def toQueryObj(self):
        return {"invoker": self.invoker, "contract_id": self.contract_id, "tx_id": self.tx_id, \
                "contract_type": self.contract_type, "quote_amount": self.quote_amount, \
                "block_num": self.block_num, "timestamp": self.timestamp}


class CrossChainAssetInOut(db.Model):
    __tablename__ = 'cross_chain_asset_in_out'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    tx_id = db.Column(db.String(64), nullable=False, index=True)
    sign_tx_id = db.Column(db.String(64), default='', index=True)
    combine_tx_id = db.Column(db.String(64), default='')
    cross_chain_tx_id = db.Column(db.Text, default='')
    cross_chain_from = db.Column(db.String(64), default='')
    cross_chain_to = db.Column(db.Text, default='')
    cross_chain_block_num = db.Column(db.Integer, default=0)
    amount = db.Column(db.BigInteger)
    asset_id = db.Column(db.String(64))
    asset_symbol = db.Column(db.String(64))
    hx_address = db.Column(db.String(64))
    block_num = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime)

    def __init__(self, **kwargs):
        super(CrossChainAssetInOut, self).__init__(**kwargs)

    def __repr__(self):
        return '<CrossChainAssetInOut %r>' % self.tx_id
    
    def toQueryObj(self):
        return {"tx_id": self.tx_id, "cross_chain_tx_id": self.cross_chain_tx_id, \
                "cross_chain_from": self.cross_chain_from, "sign_tx_id": self.sign_tx_id, \
                "cross_chain_to": self.cross_chain_to, "asset_id": self.asset_id, "asset_symbol": self.asset_symbol, \
                "deposit_address": self.deposit_address, "amount": self.amount, "block_num": self.block_num, \
                "timestamp": self.timestamp, "combine_tx_id": self.combine_tx_id}


class ContractExchangeOrder(db.Model):
    __tablename__ = 'contract_exchange_order'
    id = db.Column(db.Integer, primary_key=True)
    address = db.Column(db.String(64), index=True)
    ex_pair = db.Column(db.String(64), index=True)
    ex_type = db.Column(db.String(8))
    base_amount = db.Column(db.BigInteger)
    quote_amount = db.Column(db.BigInteger)
    tx_id = db.Column(db.String(64), index=True)
    block_num = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime)

    def __init__(self, **kwargs):
        super(ContractExchangeOrder, self).__init__(**kwargs)

    def __repr__(self):
        return '<ContractExchangeOrder %r>' % self.contract_address
    
    def toQueryObj(self):
        return {"base_amount": self.base_amount, "quote_amount": self.quote_amount, \
                "ex_pair": self.ex_pair, "ex_type": self.ex_type, "tx_id": self.tx_id}


class TxContractDealHistory(db.Model):
    __tablename__ = 'tx_contract_deal_history'
    id = db.Column(db.Integer, primary_key=True)
    address = db.Column(db.String(64), index=True)
    tx_id = db.Column(db.String(64), index=True)
    match_tx_id = db.Column(db.String(64), index=True)
    base_amount = db.Column(db.BigInteger)
    quote_amount = db.Column(db.BigInteger)
    ex_type = db.Column(db.String(8))
    ex_pair = db.Column(db.String(64), index=True)
    block_num = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime)

    def __init__(self, **kwargs):
        super(TxContractDealHistory, self).__init__(**kwargs)

    def __repr__(self):
        return '<TxContractDealHistory %r>' % self.tx_id
    
    def toQueryObj(self):
        return {"addr": self.address, "pair": self.ex_pair, "base_amount": self.base_amount, \
                "quote_amount": self.quote_amount, "block_num": self.block_num, \
                "timestamp": self.timestamp}


class TxContractDealTick(db.Model):
    __tablename__ = 'tx_contract_deal_tick'
    id = db.Column(db.Integer, primary_key=True)
    tx_id = db.Column(db.String(64), index=True)
    base_amount = db.Column(db.BigInteger)
    quote_amount = db.Column(db.BigInteger)
    ex_pair = db.Column(db.String(64), index=True)
    block_num = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime)

    def __init__(self, **kwargs):
        super(TxContractDealTick, self).__init__(**kwargs)

    def __repr__(self):
        return '<TxContractDealTick %r>' % self.tx_id
    
    def toQueryObj(self):
        return {"pair": self.ex_pair, "base_amount": self.base_amount, \
                "quote_amount": self.quote_amount, "block_num": self.block_num, \
                "timestamp": self.timestamp}


class TxContractDealKdata1Min(db.Model):
    __tablename__ = 'tx_contract_deal_kdata_1min'
    id = db.Column(db.Integer, primary_key=True)
    ex_pair = db.Column(db.String(64), index=True)
    k_open = db.Column(db.Float)
    k_close = db.Column(db.Float)
    k_low = db.Column(db.Float)
    k_high = db.Column(db.Float)
    base_amount = db.Column(db.BigInteger)
    quote_amount = db.Column(db.BigInteger)
    block_num = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime)

    def __init__(self, **kwargs):
        super(TxContractDealKdata1Min, self).__init__(**kwargs)

    def __repr__(self):
        return '<TxContractDealKdata1Min %r>' % self.tx_id
    
    def toQueryObj(self):
        return {"ex_pair": self.ex_pair, "k_open": self.k_open, "k_close": self.k_close, "k_low": self.k_low, \
                "k_high": self.k_high, "block_num": self.block_num, "base_amount": self.base_amount, \
                "quote_amount": self.quote_amount, "timestamp": self.timestamp}


class TxContractDealKdata5Min(db.Model):
    __tablename__ = 'tx_contract_deal_kdata_5min'
    id = db.Column(db.Integer, primary_key=True)
    ex_pair = db.Column(db.String(64), index=True)
    k_open = db.Column(db.Float)
    k_close = db.Column(db.Float)
    k_low = db.Column(db.Float)
    k_high = db.Column(db.Float)
    base_amount = db.Column(db.BigInteger)
    quote_amount = db.Column(db.BigInteger)
    block_num = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime)

    def __init__(self, **kwargs):
        super(TxContractDealKdata5Min, self).__init__(**kwargs)

    def __repr__(self):
        return '<TxContractDealKdata5Min %r>' % self.tx_id
    
    def toQueryObj(self):
        return {"ex_pair": self.ex_pair, "k_open": self.k_open, "k_close": self.k_close, "k_low": self.k_low, \
                "k_high": self.k_high, "block_num": self.block_num, "base_amount": self.base_amount, \
                "quote_amount": self.quote_amount, "timestamp": self.timestamp}


class TxContractDealKdata15Min(db.Model):
    __tablename__ = 'tx_contract_deal_kdata_15min'
    id = db.Column(db.Integer, primary_key=True)
    ex_pair = db.Column(db.String(64), index=True)
    k_open = db.Column(db.Float)
    k_close = db.Column(db.Float)
    k_low = db.Column(db.Float)
    k_high = db.Column(db.Float)
    base_amount = db.Column(db.BigInteger)
    quote_amount = db.Column(db.BigInteger)
    block_num = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime)

    def __init__(self, **kwargs):
        super(TxContractDealKdata15Min, self).__init__(**kwargs)

    def __repr__(self):
        return '<TxContractDealKdata15Min %r>' % self.tx_id
    
    def toQueryObj(self):
        return {"ex_pair": self.ex_pair, "k_open": self.k_open, "k_close": self.k_close, "k_low": self.k_low, \
                "k_high": self.k_high, "block_num": self.block_num, "base_amount": self.base_amount, \
                "quote_amount": self.quote_amount, "timestamp": self.timestamp}


class TxContractDealKdata30Min(db.Model):
    __tablename__ = 'tx_contract_deal_kdata_30min'
    id = db.Column(db.Integer, primary_key=True)
    ex_pair = db.Column(db.String(64), index=True)
    k_open = db.Column(db.Float)
    k_close = db.Column(db.Float)
    k_low = db.Column(db.Float)
    k_high = db.Column(db.Float)
    base_amount = db.Column(db.BigInteger)
    quote_amount = db.Column(db.BigInteger)
    block_num = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime)

    def __init__(self, **kwargs):
        super(TxContractDealKdata30Min, self).__init__(**kwargs)

    def __repr__(self):
        return '<TxContractDealKdata30Min %r>' % self.tx_id
    
    def toQueryObj(self):
        return {"ex_pair": self.ex_pair, "k_open": self.k_open, "k_close": self.k_close, "k_low": self.k_low, \
                "k_high": self.k_high, "block_num": self.block_num, "base_amount": self.base_amount, \
                "quote_amount": self.quote_amount, "timestamp": self.timestamp}


class TxContractDealKdata1Hour(db.Model):
    __tablename__ = 'tx_contract_deal_kdata_1hour'
    id = db.Column(db.Integer, primary_key=True)
    ex_pair = db.Column(db.String(64), index=True)
    k_open = db.Column(db.Float)
    k_close = db.Column(db.Float)
    k_low = db.Column(db.Float)
    k_high = db.Column(db.Float)
    base_amount = db.Column(db.BigInteger)
    quote_amount = db.Column(db.BigInteger)
    block_num = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime)

    def __init__(self, **kwargs):
        super(TxContractDealKdata1Hour, self).__init__(**kwargs)

    def __repr__(self):
        return '<TxContractDealKdata1Hour %r>' % self.tx_id
    
    def toQueryObj(self):
        return {"ex_pair": self.ex_pair, "k_open": self.k_open, "k_close": self.k_close, "k_low": self.k_low, \
                "k_high": self.k_high, "block_num": self.block_num, "base_amount": self.base_amount, \
                "quote_amount": self.quote_amount, "timestamp": self.timestamp}


class TxContractDealKdata2Hour(db.Model):
    __tablename__ = 'tx_contract_deal_kdata_2hour'
    id = db.Column(db.Integer, primary_key=True)
    ex_pair = db.Column(db.String(64), index=True)
    k_open = db.Column(db.Float)
    k_close = db.Column(db.Float)
    k_low = db.Column(db.Float)
    k_high = db.Column(db.Float)
    base_amount = db.Column(db.BigInteger)
    quote_amount = db.Column(db.BigInteger)
    block_num = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime)

    def __init__(self, **kwargs):
        super(TxContractDealKdata2Hour, self).__init__(**kwargs)

    def __repr__(self):
        return '<TxContractDealKdata2Hour %r>' % self.tx_id
    
    def toQueryObj(self):
        return {"ex_pair": self.ex_pair, "k_open": self.k_open, "k_close": self.k_close, "k_low": self.k_low, \
                "k_high": self.k_high, "block_num": self.block_num, "base_amount": self.base_amount, \
                "quote_amount": self.quote_amount, "timestamp": self.timestamp}


class TxContractDealKdata6Hour(db.Model):
    __tablename__ = 'tx_contract_deal_kdata_6hour'
    id = db.Column(db.Integer, primary_key=True)
    ex_pair = db.Column(db.String(64), index=True)
    k_open = db.Column(db.Float)
    k_close = db.Column(db.Float)
    k_low = db.Column(db.Float)
    k_high = db.Column(db.Float)
    base_amount = db.Column(db.BigInteger)
    quote_amount = db.Column(db.BigInteger)
    block_num = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime)

    def __init__(self, **kwargs):
        super(TxContractDealKdata6Hour, self).__init__(**kwargs)

    def __repr__(self):
        return '<TxContractDealKdata6Hour %r>' % self.tx_id
    
    def toQueryObj(self):
        return {"ex_pair": self.ex_pair, "k_open": self.k_open, "k_close": self.k_close, "k_low": self.k_low, \
                "k_high": self.k_high, "block_num": self.block_num, "base_amount": self.base_amount, \
                "quote_amount": self.quote_amount, "timestamp": self.timestamp}


class TxContractDealKdata12Hour(db.Model):
    __tablename__ = 'tx_contract_deal_kdata_12hour'
    id = db.Column(db.Integer, primary_key=True)
    ex_pair = db.Column(db.String(64), index=True)
    k_open = db.Column(db.Float)
    k_close = db.Column(db.Float)
    k_low = db.Column(db.Float)
    k_high = db.Column(db.Float)
    base_amount = db.Column(db.BigInteger)
    quote_amount = db.Column(db.BigInteger)
    block_num = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime)

    def __init__(self, **kwargs):
        super(TxContractDealKdata12Hour, self).__init__(**kwargs)

    def __repr__(self):
        return '<TxContractDealKdata12Hour %r>' % self.tx_id
    
    def toQueryObj(self):
        return {"ex_pair": self.ex_pair, "k_open": self.k_open, "k_close": self.k_close, "k_low": self.k_low, \
                "k_high": self.k_high, "block_num": self.block_num, "base_amount": self.base_amount, \
                "quote_amount": self.quote_amount, "timestamp": self.timestamp}


class TxContractDealKdataDaily(db.Model):
    __tablename__ = 'tx_contract_deal_kdata_daily'
    id = db.Column(db.Integer, primary_key=True)
    ex_pair = db.Column(db.String(64), index=True)
    k_open = db.Column(db.Float)
    k_close = db.Column(db.Float)
    k_low = db.Column(db.Float)
    k_high = db.Column(db.Float)
    base_amount = db.Column(db.BigInteger)
    quote_amount = db.Column(db.BigInteger)
    block_num = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime)

    def __init__(self, **kwargs):
        super(TxContractDealKdataDaily, self).__init__(**kwargs)

    def __repr__(self):
        return '<TxContractDealKdataDaily %r>' % self.tx_id
    
    def toQueryObj(self):
        return {"ex_pair": self.ex_pair, "k_open": self.k_open, "k_close": self.k_close, "k_low": self.k_low, \
                "k_high": self.k_high, "block_num": self.block_num, "base_amount": self.base_amount, \
                "quote_amount": self.quote_amount, "timestamp": self.timestamp}


class TxContractDealKdataWeekly(db.Model):
    __tablename__ = 'tx_contract_deal_kdata_weekly'
    id = db.Column(db.Integer, primary_key=True)
    ex_pair = db.Column(db.String(64), index=True)
    k_open = db.Column(db.Float)
    k_close = db.Column(db.Float)
    k_low = db.Column(db.Float)
    k_high = db.Column(db.Float)
    base_amount = db.Column(db.BigInteger)
    quote_amount = db.Column(db.BigInteger)
    block_num = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime)

    def __init__(self, **kwargs):
        super(TxContractDealKdataWeekly, self).__init__(**kwargs)

    def __repr__(self):
        return '<TxContractDealKdataWeekly %r>' % self.tx_id
    
    def toQueryObj(self):
        return {"ex_pair": self.ex_pair, "k_open": self.k_open, "k_close": self.k_close, "k_low": self.k_low, \
                "k_high": self.k_high, "block_num": self.block_num, "base_amount": self.base_amount, \
                "quote_amount": self.quote_amount, "timestamp": self.timestamp}


class TxContractDealKdataMonthly(db.Model):
    __tablename__ = 'tx_contract_deal_kdata_monthly'
    id = db.Column(db.Integer, primary_key=True)
    ex_pair = db.Column(db.String(64), index=True)
    k_open = db.Column(db.Float)
    k_close = db.Column(db.Float)
    k_low = db.Column(db.Float)
    k_high = db.Column(db.Float)
    base_amount = db.Column(db.BigInteger)
    quote_amount = db.Column(db.BigInteger)
    block_num = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime)

    def __init__(self, **kwargs):
        super(TxContractDealKdataMonthly, self).__init__(**kwargs)

    def __repr__(self):
        return '<TxContractDealKdataMonthly %r>' % self.tx_id
    
    def toQueryObj(self):
        return {"ex_pair": self.ex_pair, "k_open": self.k_open, "k_close": self.k_close, "k_low": self.k_low, \
                "k_high": self.k_high, "block_num": self.block_num, "base_amount": self.base_amount, \
                "quote_amount": self.quote_amount, "timestamp": self.timestamp}


class ContractPersonExchangeEvent(db.Model):
    __tablename__ = 'contract_person_exchange_event'
    id = db.Column(db.Integer, primary_key=True)
    caller_addr = db.Column(db.String(64), index=True)
    contract_address = db.Column(db.String(64), index=True)
    tx_id = db.Column(db.String(64), index=True)
    event_name = db.Column(db.String(64), index=True)
    event_arg = db.Column(db.Text)
    op_num = db.Column(db.Integer)
    block_num = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime)

    def __init__(self, **kwargs):
        super(ContractPersonExchangeEvent, self).__init__(**kwargs)

    def __repr__(self):
        return '<ContractPersonExchangeEvent %r>' % self.tx_id
    
    def toQueryObj(self):
        return {"caller_addr": self.caller_addr, "event_name": self.event_name, "tx_id": self.tx_id, \
                "event_arg": self.event_arg, "block_num": self.block_num, "timestamp": self.timestamp}


class ContractPersonExchangeOrder(db.Model):
    __tablename__ = 'contract_person_exchange_order'
    id = db.Column(db.Integer, primary_key=True)
    contract_address = db.Column(db.String(64), index=True)
    from_asset = db.Column(db.String(64))
    to_asset = db.Column(db.String(64))
    from_supply = db.Column(db.BigInteger)
    to_supply = db.Column(db.BigInteger)
    price = db.Column(db.String(64), index=True)

    def __init__(self, **kwargs):
        super(ContractPersonExchangeOrder, self).__init__(**kwargs)

    def __repr__(self):
        return '<ContractPersonExchangeOrder %r>' % self.contract_address
    
    def toQueryObj(self):
        return {"contract_address": self.contract_address, "from_asset": self.from_asset, "to_asset": self.to_asset, \
                "from_supply": str(self.from_supply), "to_supply": str(self.to_supply), "price": self.price}


class BlockRawHistory(db.Model):
    __tablename__ = 'block_raw_history'
    id = db.Column(db.Integer, primary_key=True)
    block_num = db.Column(db.Integer)
    block_id = db.Column(db.String(64), index=True)
    prev_id = db.Column(db.String(64))
    timestamp = db.Column(db.DateTime)
    trxfee = db.Column(db.String(64))
    miner = db.Column(db.String(64))
    next_secret_hash = db.Column(db.String(64))
    previous_secret = db.Column(db.String(64))
    reward = db.Column(db.String(64))
    signing_key = db.Column(db.Text)

    def __init__(self, **kwargs):
        super(BlockRawHistory, self).__init__(**kwargs)

    def __repr__(self):
        return '<BlockRawHistory %r>' % self.block_id

kline_table_list = [
    TxContractDealKdata1Min, 
    TxContractDealKdata5Min,
    TxContractDealKdata15Min,
    TxContractDealKdata30Min,
    TxContractDealKdata1Hour,
    TxContractDealKdata2Hour,
    TxContractDealKdata6Hour,
    TxContractDealKdata12Hour,
    TxContractDealKdataDaily,
    TxContractDealKdataWeekly,
    TxContractDealKdataMonthly
]
