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

class IntrusionDetection(Base):
    def __init__(self, client, device, id, name=None):
        self.client = client
        self.device = device
        self.id = id
        self.name = name
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
     
    @property
    def get_device(self):
        """Retrieve device of Intrusion Detection"""
        return self.device
    
    def update(self):
        try:
            self.load( self.client.request("smarthome/devices/intrusionDetectionSystem/services/IntrusionDetectionControl/state") )
            return True
        except ErrorException:
            return False

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

    def arm_activation_delay(self, seconds):
        """Set the arm activation delay time the intrusion detection system."""
        if operation_state == operation_state.SYSTEM_ARMING:
            return False
        
        data = {'@type': 'intrusionDetectionControlState',
                'armActivationDelayTime': seconds}
        try:
            self.client.request("smarthome/devices/intrusionDetectionSystem/services/IntrusionDetectionControl/state", method='PUT', params=data)
            return True
        except ErrorException:
            return False

    def arm_instant(self):
        """Set an instant arm activation of the intrusion detection system."""
        if operation_state == operation_state.SYSTEM_ARMING:
            return False

        delay_time = self.armActivationDelayTime
        self.arm_activation_delay(1)
        self.arm()
        self.arm_activation_delay(delay_time)

    def mute_alarm(self):
        """Mute the alarm of the intrusion detection system."""
        return self.setOperationState(operation_state.MUTE_ALARM)
    
    def trigger(self):
        # not implemented yet
        print("Trigger alarm simulation")

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
    
def initialize_intrusion_detection(client, device_list):
    """Helper function to initialize intrusion detection given from a device list."""
    for item in device_list.items:
        if item.deviceModel == "INTRUSION_DETECTION_SYSTEM":
            return IntrusionDetection(client, item, item.id, item.name)
