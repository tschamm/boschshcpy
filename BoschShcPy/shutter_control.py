from enum import Enum, auto

from BoschShcPy.base import Base
from BoschShcPy.base_list import BaseList
from BoschShcPy.client import ErrorException
from BoschShcPy.device import Device, status_rx

class operation_state(Enum):
    STOPPED = auto()
    MOVING = auto()
    CALIBRATING = auto()
    
operation_state_rx = {'STOPPED': operation_state.STOPPED, 'MOVING': operation_state.MOVING, 'CALIBRATING': operation_state.CALIBRATING}
operation_state_tx = {operation_state.STOPPED: 'STOPPED', operation_state.MOVING: 'MOVING', operation_state.CALIBRATING: 'CALIBRATING'}

class ShutterControl(Base):
    def __init__(self, client, device, id, name=None):
        self.client = client
        self.device = device
        self.id = id
        self.name = name
        self.type = None
        self.operationState = 'STOPPED'
        self.level = None
#         self.update()

    @property
    def get_state(self):
        """Retrieve state of Shutter Control."""
        return operation_state_rx[self.operationState]

    @property
    def get_name(self):
        """Retrieve name of Shutter Control"""
        return self.name
    
    @property
    def get_id(self):
        """Retrieve id of Shutter Control"""
        return self.id
    
    @property
    def get_device(self):
        """Retrieve device of Smart Plug"""
        return self.device
    
    @property
    def get_level(self):
        """Retrieve level of Shutter Control"""
        return self.level
    
    @property
    def get_availability(self):
        return status_rx[self.device.status]
    
    def update(self):
        try:
            self.load( self.client.request("smarthome/devices/"+self.id+"/services/ShutterControl/state") )
#             print("Update request received")
#             print(self)
            return True
        except ErrorException:
            return False

    def update_from_query(self, query_result):
        if query_result['id'] != "ShutterControl":
            return False
        
        if self.id != query_result['deviceId'] or query_result['state']['@type'] != "shutterControlState":
            print("Wrong device id %s or state type %s" % (query_result['deviceId'], query_result['state']['@type']))
            return False
        
        self.operationState = query_result['state']['operationState']
        
        """As info is delayed, only update level if shutter control is not moving to prevent flickering"""
        if self.operationState == 'STOPPED':        
            self.level = query_result['state']['level']
        return True
    
    def set_level(self, level):
        """Set a new level of Shutter Control."""
        data={'@type':'shutterControlState', 'level': level}
        try:
            self.client.request("smarthome/devices/"+self.id+"/services/ShutterControl/state", method='PUT', params=data)
            self.level = level
#             self.update()
            return True
        except ErrorException:
            return False

    def stop(self):
        """Stops movement of Shutter Control."""
#         data={'@type':'shutterControlState', 'calibrated': True, 'operationState': operation_state_tx[operation_state.STOPPED]}
        try:
            self.client.request("smarthome/shading/shutters/"+self.id+"/stop", method='PUT')
#             self.update()
            return True
        except ErrorException:
            return False
    
#     def get_services(self):
#         """Retrieve services of Shutter Control."""
#         return SmartPlugServices().load(self.client.request("smarthome/devices/"+self.id+"/services"))

    def __str__(self):
        return "\n".join([
            'Shutter Control:',
            '  Id                        : %s' % self.id,
            '  Name                      : %s' % self.name,
            '  operationState            : %s' % self.operationState,
            '  level                     : %s' % self.level, 
            '-%s' % self.device,
        ])

# b'{"@type":"shutterControlState","calibrated":true,"referenceMovingTimes":{"movingTimeTopToBottomInMillis":17680,"movingTimeBottomToTopInMillis":18080},"level":0.0,"operationState":"STOPPED","endPositionAutoDetect":true,"endPositionSupported":true,"delayCompensationTime":12.7,"delayCompensationSupported":true,"automaticDelayCompensation":true,"slatsRunningTimeInMillis":0}'

# class SmartPlugServices(BaseList):
#     def __init__(self):
#         # We're expecting items of type Device
#         super(SmartPlugServices, self).__init__(SmartPlugService)
#         
# class SmartPlugService(Base):
#     def __init__(self):
#         self.id = None
#         self.deviceId = None
#         self.state = None
#         
#     def __str__(self):
#         return "\n".join([
#             'id                     : %s' % self.id,
#             'deviceId               : %s' % self.deviceId,
#             'state                  : %s' % self.state,
#         ])

def initialize_shutter_controls(client, device_list):
    """Helper function to initialize all shutter controls given from a device list."""
    shutter_controls = []
    for item in device_list.items:
        if item.deviceModel == "BBL":
            shutter_controls.append(ShutterControl(client, item, item.id, item.name))
    return shutter_controls
