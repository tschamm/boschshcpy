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

# Code mostly taken from messagebird API, see LICENCE


import json
import requests
import logging
from os.path import isfile

# import requests_async as requests
from enum import Enum

try:
    from urllib.parse import urljoin
except ImportError:
    from urlparse import urljoin

import urllib3
urllib3.disable_warnings()

from BoschShcPy.error import ErrorException

_LOGGER = logging.getLogger(__name__)


class ResponseFormat(Enum):
    text = 1
    binary = 2

class HttpClient(object):
    """Used for sending simple HTTP requests."""

    def __init__(self, endpoint, access_cert, access_key, user_agent):
        self.__supported_status_codes = [200, 201, 204, 401, 404, 405, 422, 503]

        self.endpoint = endpoint
        self.access_cert = access_cert
        self.access_key = access_key
        self.user_agent = user_agent

    def request(self, path, method='GET', params=None, headers=None, format=ResponseFormat.text):
        """Builds a request and gets a response."""
        if params is None: params = {}
        url = urljoin(self.endpoint, path)
        if not isfile(self.access_cert) or not isfile(self.access_key):
            raise (ErrorException("Certification files not valid"))
        cert=(self.access_cert, self.access_key)
        if headers is None: headers = {
            'Content-Type': 'application/json'
        }

        response = None
        if method == "GET":
            response = requests.get(url, verify=False, cert=cert, headers=headers, params=params)
        elif method == "POST":
            response = requests.post(url, verify=False, cert=cert, headers=headers, data=json.dumps(params))
        elif method == "PUT":
            response = requests.put(url, verify=False, cert=cert, headers=headers, data=json.dumps(params))
        else:
            response = str(method) + ' is not a supported HTTP method'

        _LOGGER.debug(response.content)
        
        if isinstance(response, str):
            raise ValueError(response)

        if response.status_code not in self.__supported_status_codes:
            response.raise_for_status()

        response_switcher = {
            ResponseFormat.text: response.text,
            ResponseFormat.binary: response.content
        }
        return response_switcher.get(format)
