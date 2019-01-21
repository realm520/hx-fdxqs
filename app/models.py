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
    block_height = db.Column(db.Integer)
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

    def __init__(self, **kwargs):
        super(TxContractEventHistory, self).__init__(**kwargs)

    def __repr__(self):
        return '<TxContractEventHistory %r>' % self.tx_id


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
    block_height = db.Column(db.Integer)
    timestamp = db.Column(db.String(64))

    def __init__(self, **kwargs):
        super(TxContractDealHistory, self).__init__(**kwargs)

    def __repr__(self):
        return '<TxContractDealHistory %r>' % self.tx_id
    
    def toQueryObj(self):
        return {"addr": self.address, "pair": self.ex_pair, "base_amount": self.base_amount, \
                "quote_amount": self.quote_amount, "block_height": self.block_height, \
                "timestamp": self.timestamp}


class BlockRawHistory(db.Model):
    __tablename__ = 'block_raw_history'
    id = db.Column(db.Integer, primary_key=True)
    block_height = db.Column(db.Integer)
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

