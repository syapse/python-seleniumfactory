# Fork from the https://github.com/smartkiwi/SeleniumFactory-for-Python

"""
This class provides several helper methods to invoke the Sauce REST API.
"""

import urllib2
import json
import base64

url = 'https://saucelabs.com/rest/%s/%s/%s'


class SauceRest:
    def __init__(self, user, key):
        self.user = user
        self.key = key

    def build_url(self, version, suffix):
        return url % (version, self.user, suffix)

    def update(self, job_id, attributes):
        """
        Updates a Sauce Job with the data contained in the attributes dict
        """
        the_url = self.build_url("v1", "jobs/" + job_id)
        data = json.dumps(attributes)
        return self.invoke_put(the_url, self.user, self.key, data)

    def get(self, job_id):
        """
        Retrieves the details for a Sauce job in JSON format
        """
        the_url = self.build_url("v1", "jobs/" + job_id)
        return self.invoke_get(the_url, self.user, self.key)

    def invoke_put(self, the_url, username, password, data):
        request = urllib2.Request(the_url, data, {'content-type': 'application/json'})
        base64string = base64.encodestring('%s:%s' % (username, password))[:-1]
        request.add_header("Authorization", "Basic %s" % base64string)
        request.get_method = lambda: 'PUT'
        html_file = urllib2.urlopen(request)
        return html_file.read()

    def invoke_get(self, the_url, username, password):
        request = urllib2.Request(the_url)
        base64string = base64.encodestring('%s:%s' % (username, password))[:-1]
        request.add_header("Authorization", "Basic %s" % base64string)
        html_file = urllib2.urlopen(request)
        return html_file.read()