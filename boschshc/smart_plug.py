from boschshc.base import Base
from boschshc.base_list import BaseList

class SmartPlug(Base):
    def __init__(self):
        self.type = None
        self.switchState = None
        self.automaticPowerOffTime = None

    def __str__(self):
        return "\n".join([
            'switchState               : %s' % self.switchState,
            'automaticPowerOffTime     : %s' % self.automaticPowerOffTime,
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
