import logging

from BoschShcPy.base import Base
from BoschShcPy.client import ErrorException
from BoschShcPy.base_list import BaseList
from BoschShcPy.device import Device, status_rx

_LOGGER = logging.getLogger(__name__)

state_rx = {'ON': True, 'OFF': False}
state_tx = {True: 'ON', False: 'OFF'}
state1_rx = {'ENABLED': True, 'DISABLED': False}
state1_tx = {True: 'ENABLED', False: 'DISABLED'}

class CameraEyes(Base):
    def __init__(self, client, device, id, name=None):
        self.client = client
        self.device = device
        self.id = id
        self.name = name
        self.type = None
        self.cameraLight = 'OFF'
        self.cameraNotification = 'DISABLED'
        self.privacyMode = 'DISABLED'
        self.value = None  # caching service state

    @property
    def get_light_state(self):
        """Retrieve light state of Camera Eyes."""
        return state_rx[self.cameraLight]

    @property
    def get_name(self):
        """Retrieve name of Camera Eyes"""
        return self.name

    @property
    def get_id(self):
        """Retrieve id of Camera Eyes"""
        return self.id

    @property
    def get_device(self):
        """Retrieve device of Camera Eyes"""
        return self.device

    @property
    def get_notification_state(self):
        return state1_rx[self.cameraNotification]

    @property
    def get_privacy_state(self):
        return state1_rx[self.privacyMode]

    @property
    def get_availability(self):
        return status_rx[self.device.status]

    def update(self):
        try:
            # self.load( self.client.request("smarthome/devices/"+self.id+"/services/PrivacyMode/state") )
            # self.privacyMode = self.value
            
            result = self.client.request("smarthome/devices/"+self.id+"/services")
            print (result)
            for service_data in result:
                self.update_from_query(service_data)

            return True
        except ErrorException:
            return False

    def async_update(self, callback):
        async_update = AsyncUpdate(self.client)
        async_update.register(self, callback)
        async_update.start("smarthome/devices/"+self.id+"/services/services")
        async_update.stop
        return True

    def update_privacymode(self, query_result):
        """Retrieve privacy mode state values of Camera Eyes from polling query."""
        if self.id != query_result['deviceId'] or query_result['state']['@type'] != "privacyModeState":
            _LOGGER.error("Wrong device id %s or state type %s" % (
                query_result['deviceId'], query_result['state']['@type']))
            return False

        self.privacyMode = query_result['state']['value']
        return True

    def update_cameranotification(self, query_result):
        """Retrieve camera notification state values of Camera Eyes from polling query."""
        if self.id != query_result['deviceId'] or query_result['state']['@type'] != "cameraNotificationState":
            _LOGGER.error("Wrong device id %s or state type %s" % (
                query_result['deviceId'], query_result['state']['@type']))
            return False

        self.cameraNotification = query_result['state']['value']
        return True

    def update_cameralight(self, query_result):
        """Retrieve camera light state values of Camera Eyes from polling query."""
        if self.id != query_result['deviceId'] or query_result['state']['@type'] != "cameraLightState":
            _LOGGER.error("Wrong device id %s or state type %s" % (
                query_result['deviceId'], query_result['state']['@type']))
            return False

        self.cameraLight = query_result['state']['value']
        return True

    def update_from_query(self, query_result):
        if query_result['id'] == "PrivacyMode":
            self.update_privacymode(query_result)
        if query_result['id'] == "CameraNotification":
            self.update_cameranotification(query_result)
        if query_result['id'] == "CameraLight":
            self.update_cameralight(query_result)

    def set_light_state(self, state):
        """Set a new light state of Camera Eyes."""
        data = {'@type': 'cameraLightState', 'value': state_tx[state]}
        try:
            self.client.request("smarthome/devices/"+self.id +
                                "/services/CameraLight/state", method='PUT', params=data)
            self.cameraLight = state_tx[state]
            return True
        except ErrorException as e:
            _LOGGER.debug("Request failed with error {}".format(e))
            return False

    def get_services(self):
        """Retrieve services of Camera Eyes."""
        return CameraEyesServices().load(self.client.request("smarthome/devices/"+self.id+"/services"))

    def __str__(self):
        return "\n".join([
            'Camera Eyes:',
            '  Id                        : %s' % self.id,
            '  Name                      : %s' % self.name,
            '  cameraLight               : %s' % self.cameraLight,
            '  cameraNotification        : %s' % self.cameraNotification,
            '  privacyMode               : %s' % self.privacyMode,
            '-%s' % self.device,
        ])

class CameraEyesServices(BaseList):
    def __init__(self):
        # We're expecting items of type Device
        super(CameraEyesServices, self).__init__(CameraEyesService)

class CameraEyesService(Base):
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

def initialize_camera_eyes(client, device_list):
    """Helper function to initialize all Camera Eyes given from a device list."""
    camera_eyes = []
    for item in device_list.items:
        if item.deviceModel == "CAMERA_EYES":
            camera_eyes.append(CameraEyes(client, item, item.id, item.name))
    return camera_eyes
