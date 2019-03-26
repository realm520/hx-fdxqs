import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard to guess string'
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True  # commit to database after each reqeust/response
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_RECORD_QUERIES = True
    FLASK_DB_QUERY_TIMEOUT = 0
    WORK_DIR = basedir

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    DEBUG = True
    # HX_RPC_ENDPOINT = "http://127.0.0.1:50321"
    HX_RPC_ENDPOINT = "http://192.168.1.121:30088"
    MARKET_SOURCE = 'http://api.zb.cn/data/v1/'
    CONTRACT_EXCHANGE_ID = [r'HXCZXisggrbv8wgF4qGyJFttQuv7P8GG3H6E']
    CONTRACT_EXCHANGE_PAIRS = ['ERCPAX/HX', 'HC/HX']
    CONTRACT_CALLER = 'test002'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'data-dev.sqlite')


class TestingConfig(Config):
    HX_RPC_ENDPOINT = "http://132.232.21.36:8099"
    MARKET_SOURCE = 'http://api.zb.cn/data/v1/'
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'data-test.sqlite')


class ProductionConfig(Config):
    HX_RPC_ENDPOINT = "http://127.0.0.1:8099"
    CONTRACT_CALLER = 'order'
    MARKET_SOURCE = 'http://api.zb.cn/data/v1/'
    CONTRACT_EXCHANGE_ID = ["HXCRCnJ8AV624UZBLNKz4UBweVbhVXkQfNe7"]
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'postgresql://fdxqs:HyperExchange2019#@localhost/fdxqs'


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,

    'default': DevelopmentConfig
}
