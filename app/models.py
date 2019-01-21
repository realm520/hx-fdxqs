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
    tx_type = db.Column(db.String(64))
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


class ContractInfo(db.Model):
    __tablename__ = 'contract_info'
    id = db.Column(db.Integer, primary_key=True)
    invoker = db.Column(db.String(64), index=True)
    contract_id = db.Column(db.String(64), index=True)
    tx_id = db.Column(db.String(64))
    abi = db.Column(db.Text)
    offline_abi = db.Column(db.Text)
    code_hash = db.Column(db.String(64))
    contract_type = db.Column(db.String(8))
    block_num = db.Column(db.Integer)
    timestamp = db.Column(db.String(64))

    def __init__(self, **kwargs):
        super(ContractInfo, self).__init__(**kwargs)

    def __repr__(self):
        return '<ContractInfo %r>' % self.tx_id
    
    def toQueryObj(self):
        return {"invoker": self.invoker, "contract_id": self.contract_id, "tx_id": self.tx_id, \
                "contract_type": self.contract_type, "quote_amount": self.quote_amount, \
                "block_num": self.block_num, "timestamp": self.timestamp}


class TxContractDealHistory(db.Model):
    __tablename__ = 'tx_contract_deal_history'
    id = db.Column(db.Integer, primary_key=True)
    address = db.Column(db.String(64), index=True)
    tx_id = db.Column(db.String(64), index=True)
    match_tx_id = db.Column(db.String(64), index=True)
    base_amount = db.Column(db.Integer)
    quote_amount = db.Column(db.Integer)
    ex_type = db.Column(db.String(8))
    ex_pair = db.Column(db.String(64), index=True)
    block_num = db.Column(db.Integer)
    timestamp = db.Column(db.String(64))

    def __init__(self, **kwargs):
        super(TxContractDealHistory, self).__init__(**kwargs)

    def __repr__(self):
        return '<TxContractDealHistory %r>' % self.tx_id
    
    def toQueryObj(self):
        return {"addr": self.address, "pair": self.ex_pair, "base_amount": self.base_amount, \
                "quote_amount": self.quote_amount, "block_num": self.block_num, \
                "timestamp": self.timestamp}


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
    timestamp = db.Column(db.String(64))

    def __init__(self, **kwargs):
        super(ContractPersonExchangeEvent, self).__init__(**kwargs)

    def __repr__(self):
        return '<ContractPersonExchangeEvent %r>' % self.tx_id
    
    def toQueryObj(self):
        return {"caller_addr": self.caller_addr, "event_name": self.event_name, "tx_id": self.tx_id, \
                "event_arg": self.event_arg, "block_num": self.block_num, "timestamp": self.timestamp}


class BlockRawHistory(db.Model):
    __tablename__ = 'block_raw_history'
    id = db.Column(db.Integer, primary_key=True)
    block_num = db.Column(db.Integer)
    block_id = db.Column(db.String(64), index=True)
    prev_id = db.Column(db.String(64))
    timestamp = db.Column(db.String(64))
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

