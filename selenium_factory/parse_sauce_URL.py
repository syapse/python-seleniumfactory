# Fork from the https://github.com/smartkiwi/SeleniumFactory-for-Python

import json


class ParseSauceURL:
    def __init__(self, url):
        self.url = url

        self.fields = {}
        fields = self.url.split(':')[1][1:].split('&')
        for field in fields:
            [key, value] = field.split('=')
            self.fields[key] = value

    def get_value(self, key):
        return self.fields.get(key, "")

    def get_user_name(self):
        return self.get_value("username")

    def get_access_key(self):
        return self.get_value("access-key")

    def get_job_name(self):
        return self.get_value("job-name")

    def get_os(self):
        return self.get_value("os")

    def get_browser(self):
        return self.get_value('browser')

    def get_browser_version(self):
        return self.get_value('browser-version')

    def get_platform(self):
        return self.get_value('platform')

    def get_timezone(self):
        return self.get_value('time-zone')

    def get_firefox_profile_url(self):
        return self.get_value('firefox-profile-url')

    def get_max_duration(self):
        try:
            return int(self.get_value('max-duration'))
        except ValueError, _:
            return 0

    def get_idle_timeout(self):
        try:
            return int(self.get_value('idle-timeout'))
        except ValueError, _:
            return 0

    def get_screen_resolution(self):
        try:
            return int(self.get_value('screen-resolution'))
        except ValueError, _:
            return "1024x768"

    def get_user_extensions_url(self):
        return self.get_value('user-extensions-url')

    def to_json(self):
        return json.dumps(self.fields, sort_keys=False)