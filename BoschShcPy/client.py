# Copyright(c) 2014, MessageBird
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:

# 1. Redistributions of source code must retain the above copyright notice, this
# list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES
#  LOSS OF USE, DATA, OR PROFITS
#  OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

# Part of the code taken from messagebird API, see LICENCE

import sys
import json
import io

from BoschShcPy.shc_information import ShcInformation
from BoschShcPy.device import Device, DeviceList
from BoschShcPy.subscribe import Subscription
from BoschShcPy.error import ErrorException

# from BoschShcPy.error import Error
from BoschShcPy.http_client import HttpClient, ResponseFormat

CLIENT_VERSION = "0.0.1"
PYTHON_VERSION = '%d.%d.%d' % (sys.version_info[0], sys.version_info[1], sys.version_info[2])
USER_AGENT = 'BoschShcPy/ApiClient/%s Python/%s' % (CLIENT_VERSION, PYTHON_VERSION)

def get_uri(ip_address, port):
    return 'https://' + ip_address + ':' + port

class Client(object):

    def __init__(self, ip_address, port, access_cert, access_key, http_client=None):
        """Initializes the client with IP address and access credentials."""
        self.ip_address = ip_address
        self.port = port
        self.access_cert = access_cert
        self.access_key = access_key
        self.http_client = http_client
        self._device_list = None
        self._subscription = Subscription(self)

    def _get_http_client(self):
        if self.http_client:
            return self.http_client

        return HttpClient(get_uri(self.ip_address, self.port), self.access_cert, self.access_key, USER_AGENT)

    def request(self, path, method='GET', params=None, headers=None):
        """Builds a request, gets a response and decodes it."""
        response_text = self._get_http_client().request(path, method, params, headers)
        if not response_text:
            return response_text

        response_json = json.loads(response_text)
        
        if 'errorCode' in response_json:
            raise (ErrorException(response_json['errorCode']))

        return response_json

    def request_plain_text(self, path, method='GET', params=None, headers=None):
        """Builds a request, gets a response and returns the body."""
        response_text = self._get_http_client().request(path, method, params, headers)

        try:
            # Try to decode the response to JSON to see if the API returned any
            # errors.
            response_json = json.loads(response_text)

            if 'errorCode' in response_json:
                raise (ErrorException(response_json['errorCode']))
        except ValueError:
            # Do nothing: json.loads throws if the input string is not valid JSON,
            # which is expected. We'll just return the response body below.
            pass

        return response_text

    def request_store_as_file(self, path, filepath, method='GET', params=None):
        """Builds a request, gets a response and decodes it."""
        response_binary = self._get_http_client().request(path, method, params, ResponseFormat.binary)

        if not response_binary:
            return response_binary

        with io.open(filepath, 'wb') as f:
            f.write(response_binary)

        return filepath

    def shc_information(self):
        """Get a detailed information about the current state of the SHC."""
        shc_device = ShcInformation(self)
        shc_device.update()
        return shc_device

    def device(self, device_id):
        """Retrive device information."""
        return Device().load(self.request("smarthome/devices/"+device_id))
    
    def device_list(self):
        """Retrieve list of devices."""
        if not self._device_list:
            self._device_list = DeviceList().load(self.request("smarthome/devices"))
        return self._device_list
    
    def register_device(self, device, callback):
        self._subscription.register(device, callback)
        
    def register_device_list(self, device_list, callback):
        for device in device_list.items:
            self._subscription.register(device, callback)

    
    def start_subscription(self):
        self._subscription.start()
        
    def stop_subscription(self):
        self._subscription.stop()

#     def subscribe_polling(self):
#         """Initialize long polling by subscription."""
#         params=["com/bosch/sh/remote/*", None]
#         data=[{'jsonrpc': '2.0', 'method': 'RE/subscribe', 'id': 'boschshcpy', 'params': params}]
#         return PollingService().load(self.request("remote/json-rpc", method='POST', params=data))
# 
#     def unsubscribe_polling(self, polling_service):
#         """Unsubscribe from long polling."""
#         params=[polling_service.result]
#         data=[{'jsonrpc': '2.0', 'method': 'RE/unsubscribe', 'id': 'boschshcpy', 'params': params}]
#         return self.request("remote/json-rpc", method='POST', params=data)
# 
#     def polling(self, polling_service, time):
#         """Query long polling."""
#         params=[polling_service.result, time]
#         data=[{'jsonrpc': '2.0', 'method': 'RE/longPoll', 'id': 'boschshcpy', 'params': params}]
#         return self.request("remote/json-rpc", method='POST', params=data)
