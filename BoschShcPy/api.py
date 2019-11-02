import logging
import os.path

from BoschShcPy.client import Client
from BoschShcPy.error import ErrorException

_LOGGER = logging.getLogger(__name__)

class Api(object):
    """ Please press and hold the button at the front of the SHC until the lights are blinking before you POST the command. When the SHC is not in pairing mode, there will be a connection error."""
    
    def __init__(self, client: Client):
        """Initializes the client with IP address and access credentials."""
        self.client = client

    def register_client(self, name, password):
        if not os.path.exists(self.client.access_cert) or not os.path.exists(self.client.access_key):
            # only continue if access_cert or access_key
            return ""

        if password is None:
            return ""

        with open(self.client.access_cert, 'r') as file:
            cert = file.read().replace('\n', '').replace('-----BEGIN CERTIFICATE-----', '-----BEGIN CERTIFICATE-----\r').replace('-----END CERTIFICATE-----', '\r-----END CERTIFICATE-----')

        headers = {
            'Content-Type': 'application/json',
            'Systempassword': password
            }

        data = {'@type': 'client',
                'id': '0123456789:host012345',
                'name': name,
                'os': 'ANDROID',
                'pushNotificationToken': 'aGcmToken',
                'primaryRole': 'ROLE_RESTRICTED_CLIENT',
                'roles': [], 
                'dynamicRoles': [],
                'certificate': cert
                }
        
        try:
            response = self.client.request("smarthome/clients", method='POST', params=data, headers=headers)
            _LOGGER.debug(response)

            # check for 201, or 401 if failed
            if not 'token' in response:
                return ""
            
            return response['token']

        except ErrorException as e:
            print('\nAn error occured during new client registering:\n')



