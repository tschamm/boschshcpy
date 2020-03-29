from enum import Enum, auto
import logging

from BoschShcPy.base import Base
from BoschShcPy.base_list import BaseList
from BoschShcPy.client import ErrorException
from BoschShcPy.device import Device, status_rx

from BoschShcPy.subscribe import AsyncUpdate

_LOGGER = logging.getLogger(__name__)

class state(Enum):
    IDLE_OFF = auto()
    INTRUSION_ALARM = auto()
    SECONDARY_ALARM = auto()
    PRIMARY_ALARM = auto()

class alarm(Enum):
    INTRUSION_ALARM_ON_REQUESTED = auto()
    INTRUSION_ALARM_OFF_REQUESTED = auto()
    MUTE_SECONDARY_ALARM_REQUESTED = auto()

state_rx = {'IDLE_OFF': state.IDLE_OFF,
            'INTRUSION_ALARM': state.INTRUSION_ALARM,
            'SECONDARY_ALARM': state.SECONDARY_ALARM,
            'PRIMARY_ALARM': state.PRIMARY_ALARM
            }
state_tx = {alarm.INTRUSION_ALARM_ON_REQUESTED: 'INTRUSION_ALARM_ON_REQUESTED',
            alarm.INTRUSION_ALARM_OFF_REQUESTED: 'INTRUSION_ALARM_OFF_REQUESTED',
            alarm.MUTE_SECONDARY_ALARM_REQUESTED: 'MUTE_SECONDARY_ALARM_REQUESTED'
            }

class SmokeDetector(Base):
    def __init__(self, client, device, id, name=None):
        self.client = client
        self.device = device
        self.id = id
        self.name = name
        self.value = 'IDLE_OFF'
        self.batterylevel = None

    @property
    def get_state(self):
        """Retrieve state of Smoke Detector."""
        return state_rx[self.value]

    @property
    def get_name(self):
        """Retrieve name of Smoke Detector"""
        return self.name

    @property
    def get_id(self):
        """Retrieve id of Smoke Detector"""
        return self.id

    @property
    def get_device(self):
        """Retrieve device of Smoke Detector"""
        return self.device

    @property
    def get_batterylevel(self):
        """Retrieve battery level of Smoke Detector"""
        return self.batterylevel

    @property
    def get_availability(self):
        """Retrieve availability of Smoke Detector"""
        return status_rx[self.device.status]

    def set_state(self, state):
        """Set the alarm state of Smoke Detector"""
        data = {'@type': 'alarmState', 'state': state_tx[state]}
        try:
            self.client.request("smarthome/devices/" + self.id + "/services/Alarm/state", method='PUT',
                                params=data)
            return True
        except ErrorException as e:
            _LOGGER.debug("Request failed with error {}".format(e))
            return False

    def update(self):
        try:
            self.load( self.client.request("smarthome/devices/"+self.id+"/services/Alarm/state") )
            # self.load(self.client.request("smarthome/devices/" + self.id + "/services/BatteryLevel/state"))
            return True
        except ErrorException:
            return False

    def update_from_query(self, query_result):
        if query_result['id'] != "SmokeDetector":
            return False

        if self.id != query_result['deviceId'] or query_result['state']['@type'] != "alarmState":
            _LOGGER.error("Wrong device id %s or state type %s" % (
                query_result['deviceId'], query_result['state']['@type']))
            return False

        self.value = query_result['state']['value']
        # self.batterylevel = query_result['state']['level']

        return True

    def __str__(self):
        return "\n".join([
            'Smoke Detector:',
            '  Id                        : %s' % self.id,
            '  Name                      : %s' % self.name,
            '  State                     : %s' % self.value,
            '  Battery Level             : %s' % self.batterylevel,
            '-%s' % self.device,
        ])

def initialize_smoke_detectors(client, device_list):
    """Helper function to initialize all smoke detectors given from a device list."""
    smoke_detectors = []
    for item in device_list.items:
        if item.deviceModel == "SD":
            smoke_detectors.append(SmokeDetector(client, item, item.id, item.name))
    return smoke_detectors
