from enum import Enum, auto

from BoschShcPy.base import Base
from BoschShcPy.error import ErrorException

class state(Enum):
    NO_UPDATE_AVAILABLE = auto()
    DOWNLOADING = auto()
    UPDATE_IN_PROGRESS = auto()
    UPDATE_AVAILABLE = auto()

state_rx = {'NO_UPDATE_AVAILABLE': state.NO_UPDATE_AVAILABLE, 'DOWNLOADING': state.DOWNLOADING, 'UPDATE_IN_PROGRESS': state.UPDATE_IN_PROGRESS, 'UPDATE_AVAILABLE': state.UPDATE_AVAILABLE}
state_tx = {state.NO_UPDATE_AVAILABLE: 'NO_UPDATE_AVAILABLE', state.DOWNLOADING: 'DOWNLOADING', state.UPDATE_IN_PROGRESS: 'UPDATE_IN_PROGRESS', state.UPDATE_AVAILABLE: 'UPDATE_AVAILABLE'}

class ShcInformation(Base):
    def __init__(self, client):
        self.version = None
        self.updateState = None
        self.client = client
    
    def get_state(self):
        return state_rx[self.updateState]
   
    def update_from_query(self, query_result):
        """Currently, query is unknown to the author, so this won't work properly""" 
        if query_result['@type'] == "shc_device":
            self.load(query_result)
    
    def update(self):
        try:
            self.load( self.client.request("smarthome/information") )
            return True
        except ErrorException:
            return False
