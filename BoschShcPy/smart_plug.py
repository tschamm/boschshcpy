from BoschShcPy.base import Base
from BoschShcPy.base_list import BaseList
from BoschShcPy.client import ErrorException
from telnetlib import SE

state_rx = {'ON': True, 'OFF': False}
state_tx = {True: 'ON', False: 'OFF'}

class SmartPlug(Base):
    def __init__(self, client, id, name=None):
        self.client = client
        self.id = id
        self.name = name
        self.type = None
        self.switchState = 'OFF'
        self.automaticPowerOffTime = None
        self.powerConsumption = None
        self.energyConsumption = None
#         self.update()

    @property
    def get_state(self):
        """Retrieve state of Smart Plug."""
        return state_rx[self.switchState]

    @property
    def get_name(self):
        """Retrieve name of Smart Plug"""
        return self.name
    
    @property
    def get_id(self):
        """Retrieve id of Smart Plug"""
        return self.id
    
    @property
    def get_powerConsumption(self):
        return self.powerConsumption
    
    @property
    def get_energyConsumption(self):
        return self.energyConsumption

    def update(self):
        try:
            self.load( self.client.request("smarthome/devices/"+self.id+"/services/PowerSwitch/state") )
            self.load( self.client.request("smarthome/devices/"+self.id+"/services/PowerMeter/state") )
            return True
        except ErrorException:
            return False
    
    def update_switchstate(self, query_result):
        """Retrieve switch state values of Smart Plug from polling query."""
        if self.id != query_result['deviceId'] or query_result['state']['@type'] != "powerSwitchState":
            print("Wrong device id %s or state type %s" % (query_result['deviceId'], query_result['state']['@type']))
            return False
        
        self.switchState = query_result['state']['switchState']
        self.automaticPowerOffTime = query_result['state']['automaticPowerOffTime']
        return True

    def update_meterstate(self, query_result):
        """Retrieve meter state values of Smart Plug from polling query."""
        if self.id != query_result['deviceId'] or query_result['state']['@type'] != "powerMeterState":
            print("Wrong device id %s or state type %s" % (query_result['deviceId'], query_result['state']['@type']))
            return False
        
        self.powerConsumption = query_result['state']['powerConsumption']
        self.energyConsumption = query_result['state']['energyConsumption']        
        return True
    
    def update_from_query(self, query_result):
        if query_result['id'] == "PowerSwitch":
            self.update_switchstate(query_result)
        if query_result['id'] == "PowerMeter":
            self.update_meterstate(query_result)

    def set_state(self, state):
        """Set a new state of Smart Plug."""
        data={'@type':'powerSwitchState', 'switchState': state_tx[state]}
        try:
            self.client.request("smarthome/devices/"+self.id+"/services/PowerSwitch/state", method='PUT', params=data)
            self.switchState = state_tx[state]
#             self.update()
            return True
        except ErrorException:
            return False
    
    def get_services(self):
        """Retrieve services of Smart Plug."""
        return SmartPlugServices().load(self.client.request("smarthome/devices/"+self.id+"/services"))
    
    def __str__(self):
        return "\n".join([
            'Id                        : %s' % self.id,
            'Name                      : %s' % self.name,
            'switchState               : %s' % self.switchState,
            'automaticPowerOffTime     : %s' % self.automaticPowerOffTime,
            'powerConsumption          : %s' % self.powerConsumption,
            'energyConsumption         : %s' % self.energyConsumption,
        ])

class SmartPlugServices(BaseList):
    def __init__(self):
        # We're expecting items of type Device
        super(SmartPlugServices, self).__init__(SmartPlugService)
        
class SmartPlugService(Base):
    def __init__(self):
        self.id = None
        self.deviceId = None
        self.state = None
        
    def __str__(self):
        return "\n".join([
            'id                     : %s' % self.id,
            'deviceId               : %s' % self.deviceId,
            'state                  : %s' % self.state,
        ])

def initialize_smart_plugs(client, device_list):
    """Helper function to initialize all smart plugs given from a device list."""
    smart_plugs = []
    for item in device_list.items:
        if item.deviceModel == "PSM":
            smart_plugs.append(SmartPlug(client, item.id, item.name))
    return smart_plugs
