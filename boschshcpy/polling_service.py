from BoschShcPy.base import Base

class PollingService(Base):
    def __init__(self):
        """ Holds the polling subscription service data.
        """ 
        self.id = None
        self.result = None
        self.jsonrpc = None

    def __str__(self):
        return "\n".join([
            'id                     : %s' % self.id,
            'result                 : %s' % self.result,
            'jsonrpc                : %s' % self.jsonrpc,
        ])
    