from boschshc.base import Base
from boschshc.base_list import BaseList

class DeviceList(BaseList):
    def __init__(self):
        # We're expecting items of type Device
        super(DeviceList, self).__init__(Device)
        
class Device(Base):
  def __init__(self):
    self.id = None
    self.deviceServiceIds = None
    self.manufacturer = None
    self.deviceModel = None
    self.serial = None
    self.name = None
    self.deleted = None
    self.status = None

