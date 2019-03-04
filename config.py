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
    CONTRACT_EXCHANGE_ID = [r'HXCVxQzP5Bg1pmGnp9ddDf8B7pv2A79QqqTu', r'HXCGzXcFfPDwd1BHQj8VzBS9roLjkCdaGwUN', r'HXCXG2jDRCpLREUZ5ATwskeyBM35N1sXtC1t', r'HXCXGWuLefoZN6ACF4FCE6C3f4XKUFgXjAHr']
    CONTRACT_CALLER = 'senator2'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'data-dev.sqlite')


class TestingConfig(Config):
    HX_RPC_ENDPOINT = "http://132.232.21.36:8099"
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'data-test.sqlite')


class ProductionConfig(Config):
    HX_RPC_ENDPOINT = "http://127.0.0.1:8099"
    CONTRACT_CALLER = 'order'
    CONTRACT_EXCHANGE_ID = ["HXCUXnahWaciq1BDVHTq4KVmBjEWa9diMyLv"]
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'postgresql://fdxqs:HyperExchange2019#@localhost/fdxqs'


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,

    'default': DevelopmentConfig
}
