from BoschShcPy.base import Base
from BoschShcPy.base_list import BaseList

class DeviceList(BaseList):
    def __init__(self):
        # We're expecting items of type Device
        super(DeviceList, self).__init__(Device)
        
class Device(Base):
    def __init__(self):
        """ Initialize a shc device. Could be of device model type: 
        SD: Smoke Detector
        BBL: Shutter Control
        SWD: Shutter Contact
        WRC2: Universal Switch
        HUE_LIGHT
        PSM: Smart Plug
        CAMERA_EYES
        SMOKE_DETECTION_SYSTEM
        HUE_BRIDGE
        INTRUSION_DETECTION_SYSTEM
        HUE_LIGHT_ROOM_CONTROL
        VENTILATION_SERVICE
        PRESENCE_SIMULATION_SERVICE
        HUE_BRIDGE_MANAGER
        """ 
        self.id = None
        self.deviceServiceIds = None
        self.manufacturer = None
        self.deviceModel = None 
        self.serial = None
        self.name = None
        self.deleted = None
        self.status = None

    def __str__(self):
        return "\n".join([
            'id                     : %s' % self.id,
            'deviceServiceIds       : %s' % self.deviceServiceIds,
            'manufacturer           : %s' % self.manufacturer,
            'deviceModel            : %s' % self.deviceModel,
            'serial                 : %s' % self.serial,
            'name                   : %s' % self.name,
            'deleted                : %s' % self.deleted,
            'status                 : %s' % self.status,
        ])
    