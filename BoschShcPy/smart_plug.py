from BoschShcPy.base import Base
from BoschShcPy.base_list import BaseList
from BoschShcPy.client import ErrorException

class SmartPlug(Base):
    def __init__(self, client, id, name=None):
        self.client = client
        self.id = id
        self.name = name
        self.type = None
        self.switchState = None
        self.automaticPowerOffTime = None
        self.update()

    @property
    def get_state(self):
        """Retrieve state of Smart Plug."""
        return self.switchState

    @property
    def get_binarystate(self):
        """Retrieve state of Smart Plug."""
        if self.switchState=="ON":
            return True
        if self.switchState=="OFF":
            return False
        return False
    
    @property
    def get_name(self):
        """Retrieve name of Smart Plug"""
        return self.name
    
    @property
    def get_id(self):
        """Retrieve id of Smart Plug"""
        return self.id
    
    def update(self):
        try:
            self.load( self.client.request("smarthome/devices/"+self.id+"/services/PowerSwitch/state") )
            return True
        except ErrorException:
            return False
    
    def set_state(self, state):
        """Set a new state of Smart Plug."""
        data={'@type':'powerSwitchState', 'switchState': state}
        try:
            self.client.request("smarthome/devices/"+self.id+"/services/PowerSwitch/state", method='PUT', params=data)
            self.update()
            return True
        except ErrorException:
            return False

    def set_binarystate(self, state):
        if state:
            self.set_state('On')
        else:
            self.set_state('Off')

    # def smart_plug_services(self, smart_plug_id):
    #     """Retrieve services of Smart Plug."""
    #     return SmartPlugServices().load(self.request("smarthome/devices/"+smart_plug_id+"/services"))

    def __str__(self):
        return "\n".join([
            'Id                        : %s' % self.id,
            'Name                      : %s' % self.name,
            'switchState               : %s' % self.switchState,
            'automaticPowerOffTime     : %s' % self.automaticPowerOffTime,
        ])


def initialize_smart_plugs(client, device_list):
    smart_plugs = []
    for item in device_list.items:
        if item.deviceModel == "PSM":
            smart_plugs.append(SmartPlug(client, item.id, item.name))
    return smart_plugs
        

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
