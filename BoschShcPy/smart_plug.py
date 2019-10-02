from BoschShcPy.base import Base
from BoschShcPy.base_list import BaseList

class SmartPlug(Base):
    def __init__(self, client, id, name=None):
        self._client = client
        self.id = id
        self._name = name
        self.type = None
        self.switchState = None
        self.automaticPowerOffTime = None

    def update(self):
        self.load( self._client.request("smarthome/devices/"+self.id+"/services/PowerSwitch/state")
        )
        return True

    @property
    def state(self):
        """Retrieve state of Smart Plug."""
        return self.switchState
    
    @property
    def name(self):
        """Retrieve name of Smart Plug"""
        return self._name

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
