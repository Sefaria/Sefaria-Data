# -*- coding: utf-8 -*-

"""
The goal of this module is to speed up API calls by using functions and classes which can handle and recover
from exceptions and network crashes. Also, to provide higher level classes that reflect the structure of the
Sefaria.
"""

import urllib.request, urllib.parse, urllib.error
import urllib.request, urllib.error, urllib.parse
from urllib.error import URLError, HTTPError
from socket import timeout
import json
from sources.local_settings import *


class APIcall:
    """
    This class represents a basic API call to Sefaria. It contains all the data necessary parameters for a
    GET or POST request (as needed). This class will also hold the response of an API call, or errors if
    an exception was raised. This will give higher level functions and classes the ability to make decisions
    about how to proceed after an attempt was made to access the API.

    When instantiating a new instance of this class, a url MUST be supplied. An optional data parameter can
    be supplied in the event of a POST request.
    """

    def __init__(self, url, data=None):
        self.url = url
        self.data = data
        self.timeout = 10
        self.made_call = False


    def call(self):
        """
        Make a call to the API.
        """
        # if this is a POST request, process data
        if self.data:
            post_json = json.dumps(self.data)
            values = {'json': post_json, 'apikey': API_KEY}
            post = urllib.parse.urlencode(values)

        else:
            post = None

        req = urllib.request.Request(self.url, post)

        try:
            self.response = urllib.request.urlopen(req, timeout=self.timeout)

        except (URLError, HTTPError, timeout) as error:
            self.response = error


