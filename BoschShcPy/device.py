from BoschShcPy.base import Base
from BoschShcPy.base_list import BaseList

status_rx = {'AVAILABLE': True, 'UNAVAILABLE': False}
status_tx = {True: 'AVAILABLE', False: 'UNAVAILABLE'}

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
        self.profile = None
        self.roomId = None
    
    def get_id(self):
        return self.id
    
    def update_from_query(self, query_result):
        if query_result['@type'] == "device":
            self.load(query_result)

    def __str__(self):
        return "\n".join([
            'Device:',
            '  Id                        : %s' % self.id,
            '  deviceServiceIds          : %s' % self.deviceServiceIds,
            '  manufacturer              : %s' % self.manufacturer,
            '  deviceModel               : %s' % self.deviceModel,
            '  serial                    : %s' % self.serial,
            '  name                      : %s' % self.name,
            '  deleted                   : %s' % self.deleted,
            '  status                    : %s' % self.status,
            '  profile                   : %s' % self.profile,
            '  roomId                    : %s' % self.roomId,
        ])
    