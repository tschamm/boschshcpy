from enum import Enum, auto

from BoschShcPy.base import Base
from BoschShcPy.base_list import BaseList
from BoschShcPy.client import ErrorException
from BoschShcPy.device import Device, status_rx

class state(Enum):
    CLOSED = auto()
    OPEN = auto()
    
state_rx = {'CLOSED': state.CLOSED, 'OPEN': state.OPEN}
state_tx = {state.CLOSED: 'CLOSED', state.OPEN: 'OPEN'}

class ShutterContact(Base):
    def __init__(self, client, device, id, name=None):
        self.client = client
        self.device = device
        self.id = id
        self.name = name
        self.value = 'CLOSED'
        self.batterylevel = None
#         self.update()

    @property
    def get_state(self):
        """Retrieve state of Shutter Contact."""
        return state_rx[self.operationState]

    @property
    def get_name(self):
        """Retrieve name of Shutter Contact"""
        return self.name
    
    @property
    def get_id(self):
        """Retrieve id of Shutter Contact"""
        return self.id
    
    @property
    def get_device(self):
        """Retrieve device of Shutter Contact"""
        return self.device
    
    @property
    def get_batterylevel(self):
        """Retrieve battery level of Shutter Contact"""
        return self.batterylevel
    
    @property
    def get_availability(self):
        return status_rx[self.device.status]
    
    def update(self):
        try:
            self.load( self.client.request("smarthome/devices/"+self.id+"/services/ShutterContact/state") )
#             print("Update request received")
#             print(self)
            return True
        except ErrorException:
            return False

    def update_from_query(self, query_result):
        if query_result['id'] != "ShutterContact":
            return False
        
        if self.id != query_result['deviceId'] or query_result['state']['@type'] != "shutterContactState":
            print("Wrong device id %s or state type %s" % (query_result['deviceId'], query_result['state']['@type']))
            return False
        
        self.value = query_result['state']['value']
        
#             self.level = query_result['state']['level']
        return True
        
    def __str__(self):
        return "\n".join([
            'Shutter Contact:',
            '  Id                        : %s' % self.id,
            '  Name                      : %s' % self.name,
            '  State                     : %s' % self.value,
            '  Battery Level             : %s' % self.batterylevel, 
            '-%s' % self.device,
        ])

def initialize_shutter_contacts(client, device_list):
    """Helper function to initialize all shutter contacts given from a device list."""
    shutter_contacts = []
    for item in device_list.items:
        if item.deviceModel == "SWD":
            shutter_contacts.append(ShutterContact(client, item, item.id, item.name))
    return shutter_contacts
