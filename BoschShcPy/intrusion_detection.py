from enum import Enum, auto

from BoschShcPy.base import Base
from BoschShcPy.base_list import BaseList
from BoschShcPy.client import ErrorException
from BoschShcPy.device import Device, status_rx

class operation_state(Enum):
    SYSTEM_DISARMED = auto()
    SYSTEM_ARMING = auto()
    SYSTEM_ARMED = auto()
    MUTE_ALARM = auto()
     
operation_state_rx = {'SYSTEM_DISARMED': operation_state.SYSTEM_DISARMED,
                      'SYSTEM_ARMING': operation_state.SYSTEM_ARMING,
                      'SYSTEM_ARMED': operation_state.SYSTEM_ARMED,
                      'MUTE_ALARM': operation_state.MUTE_ALARM}
operation_state_tx = {operation_state.SYSTEM_DISARMED: 'SYSTEM_DISARMED', 
                      operation_state.SYSTEM_ARMING: 'SYSTEM_ARMING', 
                      operation_state.SYSTEM_ARMED: 'SYSTEM_ARMED',
                      operation_state.MUTE_ALARM: 'MUTE_ALARM'}

# {"@type":"intrusionDetectionControlState",
#     "value":"SYSTEM_DISARMED",
#     "triggers":[{"id":"hdm:HomeMaticIP:3014F711A00000987859CF7D","active":true,"readonly":false},
#                 {"id":"hdm:HomeMaticIP:3014F711A0000096D85A26A3","active":true,"readonly":false},
#                 {"id":"hdm:HomeMaticIP:3014F711A00000987859CF73","active":true,"readonly":false},
#                 {"id":"hdm:HomeMaticIP:3014F711A0000096D85A01CA","active":false,"readonly":false},
#                 {"id":"hdm:ZigBee:000d6f000b856cb6","active":false,"readonly":false},
#                 {"id":"hdm:HomeMaticIP:3014F711A000009A18587DB1","active":true,"readonly":false},
#                 {"id":"hdm:HomeMaticIP:3014F711A00000987859CF45","active":true,"readonly":false},
#                 {"id":"hdm:HomeMaticIP:3014F711A00000987859CF77","active":true,"readonly":false},
#                 {"id":"hdm:HomeMaticIP:3014F711A00000987859CF5E","active":true,"readonly":false}],
#     "actuators":[{"id":"intrusion:visual","active":true,"readonly":false},
#                  {"id":"intrusion:video","active":false,"readonly":false},
#                  {"id":"intrusion:siren","active":true,"readonly":false},
#                  {"id":"intrusion:push","active":true,"readonly":true}],
#     "remainingTimeUntilArmed"
#     "armActivationDelayTime":60,
#     "alarmActivationDelayTime":10}

class IntrusionDetection(Base):
    def __init__(self, client):
        self.client = client
        self.id = 'intrusionDetectionControlState'
        self.name = 'Intrusion Detection System'
        self.value = 'SYSTEM_DISARMED'
        self.actuators = []
        self.triggers = []
        self.remainingTimeUntilArmed = None
        self.armActivationDelayTime = None
        self.alarmActivationDelayTime = None
#         self.update()

    @property
    def get_state(self):
        """Retrieve state of Intrusion Detection."""
        return operation_state_rx[self.value]
 
    @property
    def get_name(self):
        """Retrieve name of Intrusion Detection"""
        return self.name
     
    @property
    def get_id(self):
        """Retrieve id of Intrusion Detection"""
        return self.id
     
#     @property
#     def get_device(self):
#         """Retrieve device of Intrusion Detection"""
#         return self.device
#     
#     @property
#     def get_level(self):
#         """Retrieve level of Intrusion Detection"""
#         return self.level
#     
#     @property
#     def get_availability(self):
#         return status_rx[self.device.status]
    
    def update(self):
        try:
            self.load( self.client.request("smarthome/devices/intrusionDetectionSystem/services/IntrusionDetectionControl/state") )
#             print("Update request received")
#             print(self)
            return True
        except ErrorException:
            return False

#     def update_from_query(self, query_result):
#         if query_result['id'] != "IntrusionDetection":
#             return False
#         
#         if self.id != query_result['deviceId'] or query_result['state']['@type'] != "shutterControlState":
#             print("Wrong device id %s or state type %s" % (query_result['deviceId'], query_result['state']['@type']))
#             return False
#         
#         self.operationState = query_result['state']['operationState']
#         
#         """As info is delayed, only update level if shutter control is not moving to prevent flickering"""
#         if self.operationState == 'STOPPED':        
#             self.level = query_result['state']['level']
#         return True
#

    def setOperationState(self, operation_state):
        """Set a new operation state of the intrusion detection system."""
        
        """Operation states are SYSTEM_ARMED, SYSTEM_DISARMED, MUTE_ALARM"""
        if operation_state == operation_state.SYSTEM_ARMING:
            return False
        
        data={'@type':'intrusionDetectionControlState', 'value': operation_state_tx[operation_state]}
        try:
            self.client.request("smarthome/devices/intrusionDetectionSystem/services/IntrusionDetectionControl/state", method='PUT', params=data)
#             self.value = operation_state_tx[operation_state]
#             self.update()
            return True
        except ErrorException:
            return False
        
    def disarm(self):
        """Disarm the intrusion detection system."""
        return self.setOperationState(operation_state.SYSTEM_DISARMED)

    def arm(self):
        """Arm the intrusion detection system."""
        return self.setOperationState(operation_state.SYSTEM_ARMED)

    def mute_alarm(self):
        """Mute the alarm of the intrusion detection system."""
        return self.setOperationState(operation_state.MUTE_ALARM)
    
    def trigger(self):
        print("Trigger alarm simulation")

# 
#     def stop(self):
#         """Stops movement of Intrusion Detection."""
#         data={'@type':'shutterControlState', 'operationState': operation_state_tx[operation_state.STOPPED]}
#         try:
#             self.client.request("smarthome/devices/"+self.id+"/services/IntrusionDetection/state", method='PUT', params=data)
# #             self.update()
#             return True
#         except ErrorException:
#             return False
    
#     def get_services(self):
#         """Retrieve services of Intrusion Detection."""
#         return SmartPlugServices().load(self.client.request("smarthome/devices/"+self.id+"/services"))

    def __str__(self):
        return "\n".join([
            'Intrusion Detection:',
            '  Value                    : %s' % self.value,
            '  Actuators                : %s' % self.actuators,
            '  Triggers                 : %s' % self.triggers, 
            '  remainingTimeUntilArmed  : %s' % self.remainingTimeUntilArmed, 
            '  armActivationDelayTime   : %s' % self.armActivationDelayTime, 
            '  alarmActivationDelayTime : %s' % self.alarmActivationDelayTime, 
        ])

    def register_polling(self, client, callback):
        client.register_device(self, callback)
    

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

# def initialize_intrusion_detections(client, device_list):
#     """Helper function to initialize all shutter controls given from a device list."""
#     intrusion_detections = []
#     for item in device_list.items:
#         if item.deviceModel == "BBL":
#             intrusion_detections.append(IntrusionDetection(client, item, item.id, item.name))
#     return intrusion_detections
