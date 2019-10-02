"""Code mostly taken from messagebird API, see LICENCE"""

import json
import requests
from enum import Enum

try:
    from urllib.parse import urljoin
except ImportError:
    from urlparse import urljoin

import urllib3
urllib3.disable_warnings()

class ResponseFormat(Enum):
    text = 1
    binary = 2


class HttpClient(object):
    """Used for sending simple HTTP requests."""

    def __init__(self, endpoint, access_cert, access_key, user_agent):
        self.__supported_status_codes = [200, 201, 204, 401, 404, 405, 422]

        self.endpoint = endpoint
        self.access_cert = access_cert
        self.access_key = access_key
        self.user_agent = user_agent

    def request(self, path, method='GET', params=None, format=ResponseFormat.text):
        """Builds a request and gets a response."""
        if params is None: params = {}
        url = urljoin(self.endpoint, path)
        cert=(self.access_cert, self.access_key)
        headers = {
            'Content-Type': 'application/json'
        }

        method_switcher = {
#             'DELETE': requests.delete(url, verify=False, headers=headers, data=json.dumps(params)),
            'GET': requests.get(url, verify=False, cert=cert, headers=headers, params=params)#,
#             'PATCH': requests.patch(url, verify=False, headers=headers, data=json.dumps(params)),
#             'POST': requests.post(url, verify=False, headers=headers, data=json.dumps(params)),
#             'PUT': requests.put(url, verify=False, headers=headers, data=json.dumps(params))
        }
        response = method_switcher.get(method, str(method) + ' is not a supported HTTP method')
#         print (response.content)
        
        if isinstance(response, str):
            raise ValueError(response)

        if response.status_code not in self.__supported_status_codes:
            response.raise_for_status()

        response_switcher = {
            ResponseFormat.text: response.text,
            ResponseFormat.binary: response.content
        }
        return response_switcher.get(format)
