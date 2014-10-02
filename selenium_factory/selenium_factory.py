# Fork from the https://github.com/smartkiwi/SeleniumFactory-for-Python

"""
This class wraps a webdriver/selenium instance.  It delegates most method calls to the underlying webdriver/selenium
instance, and provides some helper methods to set the build number and job status using the Sauce REST API.

It also outputs the Sauce Session ID, which will be parsed by the Jenkins/Bamboo plugins so as to associate the CI build with
the Sauce job.
"""

import os
import hashlib
import hmac

from selenium import webdriver
from selenium import selenium

from parse_sauce_URL import ParseSauceURL
from sauce_rest import SauceRest


class Wrapper:
    def __init__(self, selenium, parse, job_name=None):
        self.__dict__['selenium'] = selenium
        self.username = parse.get_user_name()
        self.accessKey = parse.get_access_key()
        self.jobName = job_name if job_name is not None else parse.get_job_name()

    def id(self):
        if hasattr(self.selenium, 'session_id'):
            return self.selenium.session_id
        else:
            return self.selenium.sessionId

    def dump_session_id(self):
        print "\rSauceOnDemandSessionID=%s job-name=%s" % (self.id(), self.jobName)

    def set_build_number(self, build_number):
        sauce_rest = SauceRest(self.username, self.accessKey)
        sauce_rest.update(self.id(), {'build': build_number})

    def set_tags(self, tags):
        sauce_rest = SauceRest(self.username, self.accessKey)
        sauce_rest.update(self.id(), {'tags': tags})

    def set_custom_data(self, custom_data):
        sauce_rest = SauceRest(self.username, self.accessKey)
        sauce_rest.update(self.id(), {'custom-data': custom_data})

    def job_passed(self):
        sauce_rest = SauceRest(self.username, self.accessKey)
        sauce_rest.update(self.id(), {'passed': True})

    def job_failed(self):
        sauce_rest = SauceRest(self.username, self.accessKey)
        sauce_rest.update(self.id(), {'passed': False})

    def get_public_job_link(self):
        token = hmac.new(
            "{}:{}".format(self.username, self.accessKey),
            self.id(),
            hashlib.md5
        ).hexdigest()

        return "https://saucelabs.com/jobs/{}?auth={}".format(self.id(), token)

    def get_job_link(self):
        return "https://saucelabs.com/jobs/{}".format(self.id())

    # automatic delegation:
    def __getattr__(self, attr):
        return getattr(self.selenium, attr)

    def __setattr__(self, attr, value):
        return setattr(self.selenium, attr, value)


class SeleniumFactory:
    """
      Simple interface factory to create Selenium objects, inspired by the SeleniumFactory interface
      from https://github.com/infradna/selenium-client-factory for Java.

      <p>
      Compared to directly initializing {@link com.thoughtworks.selenium.DefaultSelenium}, this additional indirection
      allows the build script or a CI server to control how you connect to the selenium.
      This makes it easier to run the same set of tests in different environments without
      modifying the test code.

      <p>
      This is analogous to how you connect to JDBC &mdash; you normally don't directly
      instantiate a specific driver, and instead you do {@link DriverManager#getConnection(String)}.
    """

    def __init__(self):
        pass

    def create(self):
        """
         Uses a driver specified by the 'SELENIUM_DRIVER' environment variable,
         and run the test against the domain specified in 'SELENIUM_URL' system property or the environment variable.
         If no variables exist, a local Selenium driver is created.
        """

        if 'SELENIUM_STARTING_URL' not in os.environ:
            starting_url = "http://saucelabs.com"
        else:
            starting_url = os.environ['SELENIUM_STARTING_URL']

        if 'SELENIUM_DRIVER' in os.environ\
                and 'SELENIUM_HOST' in os.environ\
                and 'SELENIUM_PORT' in os.environ:
            parse = ParseSauceURL(os.environ["SELENIUM_DRIVER"])
            driver = selenium(os.environ['SELENIUM_HOST'],
                              os.environ['SELENIUM_PORT'],
                              parse.to_json(), starting_url)
            driver.start()

            if parse.get_max_duration() != 0:
                driver.set_timeout(parse.get_max_duration())

            wrapper = Wrapper(driver, parse)
            wrapper.dump_session_id()
            return wrapper
        else:
            driver = selenium("localhost", 4444, "*firefox", starting_url)
            driver.start()
            return driver

    def create_web_driver(self, job_name=None, show_session_id=False):
        """
         Uses a driver specified by the 'SELENIUM_DRIVER' system property or the environment variable,
         and run the test against the domain specified in 'SELENIUM_STARTING_URL' system property or the environment variable.
         If no variables exist, a local Selenium web driver is created.
        """

        if 'SELENIUM_STARTING_URL' not in os.environ:
            starting_url = "http://saucelabs.com"
        else:
            starting_url = os.environ['SELENIUM_STARTING_URL']

        if 'SELENIUM_DRIVER' in os.environ:
            parse = ParseSauceURL(os.environ["SELENIUM_DRIVER"])

            SELENIUM_HOST = os.environ.get('SELENIUM_HOST', 'ondemand.saucelabs.com')
            SELENIUM_PORT = os.environ.get('SELENIUM_PORT', '80')

            desired_capabilities = {}
            if parse.get_browser() == 'android':
                desired_capabilities = webdriver.DesiredCapabilities.ANDROID
            elif parse.get_browser() in ['googlechrome', 'chrome']:
                desired_capabilities = webdriver.DesiredCapabilities.CHROME
            elif parse.get_browser() == 'firefox':
                desired_capabilities = webdriver.DesiredCapabilities.FIREFOX
            elif parse.get_browser() == 'htmlunit':
                desired_capabilities = webdriver.DesiredCapabilities.HTMLUNIT
            elif parse.get_browser() in ['iexplore', 'internet explorer']:
                desired_capabilities = webdriver.DesiredCapabilities.INTERNETEXPLORER
            elif parse.get_browser() == 'iphone':
                desired_capabilities = webdriver.DesiredCapabilities.IPHONE
            elif parse.get_browser() == 'iPad':
                desired_capabilities = webdriver.DesiredCapabilities.IPAD
            elif parse.get_browser() == 'opera':
                desired_capabilities = webdriver.DesiredCapabilities.OPERA
            elif parse.get_browser() == 'safari':
                desired_capabilities = webdriver.DesiredCapabilities.SAFARI
            elif parse.get_browser() == 'htmlunitjs':
                desired_capabilities = webdriver.DesiredCapabilities.HTMLUNITWITHJS
            elif parse.get_browser() == 'phantomjs':
                desired_capabilities = webdriver.DesiredCapabilities.PHANTOMJS
            else:
                desired_capabilities = webdriver.DesiredCapabilities.FIREFOX

            desired_capabilities['version'] = parse.get_browser_version()

            if parse.get_platform() is not "":
                desired_capabilities['platform'] = parse.get_platform()
            else:
                if os.getenv('SELENIUM_PLATFORM', None) is not None:
                    desired_capabilities['platform'] = os.environ['SELENIUM_PLATFORM']
                else:
                    #work around for name issues in Selenium 2
                    if 'Windows 2003' in parse.get_os():
                        desired_capabilities['platform'] = 'XP'
                    elif 'Windows 2008' in parse.get_os():
                        desired_capabilities['platform'] = 'VISTA'
                    elif 'Linux' in parse.get_os():
                        desired_capabilities['platform'] = 'LINUX'
                    else:
                        desired_capabilities['platform'] = parse.get_os()
            if job_name is not None:
                desired_capabilities['name'] = job_name
            else:
                desired_capabilities['name'] = parse.get_job_name()

            #make sure the test doesn't run forever if if the test crashes

            desired_capabilities['max-duration'] = os.environ.get('SELENIUM_MAX_DURATION', 300)
            if parse.get_max_duration() != 0:
                desired_capabilities['max-duration'] = parse.get_max_duration()

            desired_capabilities['command-timeout'] = desired_capabilities['max-duration']

            if 'SELENIUM_SCREEN_RESOLUTION' in os.environ:
                desired_capabilities['screen-resolution'] = os.environ['SELENIUM_SCREEN_RESOLUTION']
            elif parse.get_screen_resolution() != '1024x768':
                desired_capabilities['screen-resolution'] = parse.get_screen_resolution()

            desired_capabilities['idle-timeout'] = os.environ.get('SELENIUM_IDLE_TIMEOUT', 30)
            if parse.get_idle_timeout() != 0:
                desired_capabilities['idle-timeout'] = parse.get_idle_timeout()

            if 'SELENIUM_DISABLE_POPUP_HANDLER' in os.environ:
                disable_popup_handler_flag = os.environ['SELENIUM_DISABLE_POPUP_HANDLER']
                if disable_popup_handler_flag.lower() == 'true' or\
                                disable_popup_handler_flag == '1':
                    desired_capabilities["disable-popup-handler"] = True

            # additional flags
            # https://docs.saucelabs.com/reference/test-configuration/
            # record video option
            if 'SELENIUM_RECORD_VIDEO' in os.environ:
                desired_capabilities['record-video'] = os.environ['SELENIUM_RECORD_VIDEO']

            # skip uploading video on passing tests
            if 'SELENIUM_VIDEO_UPLOAD_ON_PASS' in os.environ:
                desired_capabilities['video-upload-on-pass'] =\
                    os.environ['SELENIUM_VIDEO_UPLOAD_ON_PASS']
            else:
                desired_capabilities['video-upload-on-pass'] = False

            # capture html source
            if 'SELENIUM_CAPTURE_HTML' in os.environ:
                desired_capabilities['capture-html'] = os.environ['SELENIUM_CAPTURE_HTML']
            else:
                desired_capabilities['capture-html'] = False

            # pass test through a specific tunnel
            if 'SAUCE_TUNNEL_ID' in os.environ:
                desired_capabilities['tunnel-identifier'] = os.environ['SAUCE_TUNNEL_ID']
            else:
                desired_capabilities['tunnel-identifier'] = None

            command_executor = "http://%s:%s@%s:%s/wd/hub" % (parse.get_user_name(),
                                                              parse.get_access_key(),
                                                              SELENIUM_HOST,
                                                              SELENIUM_PORT)

            driver = webdriver.Remote(desired_capabilities=desired_capabilities,
                                      command_executor=command_executor)

            wrapper = Wrapper(selenium=driver, parse=parse, job_name=job_name)

            if show_session_id:
                wrapper.dump_session_id()
            wrapper.get(starting_url)
            return wrapper
        else:
            return webdriver.Firefox()
