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

from selenium_factory.ParseSauceURL import *
from selenium_factory.SauceRest import *


class Wrapper:
    def __init__(self, selenium, parse):
        self.__dict__['selenium'] = selenium
        self.username = parse.getUserName()
        self.accessKey = parse.getAccessKey()
        self.jobName = parse.getJobName()

    def id(self):
        if hasattr(self.selenium, 'session_id'):
            return self.selenium.session_id
        else:
            return self.selenium.sessionId

    def dump_session_id(self):
        print "\rSauceOnDemandSessionID=%s job-name=%s" % (self.id(), self.jobName)

    def set_build_number(self, buildNumber):
        sauceRest = SauceRest(self.username, self.accessKey)
        sauceRest.update(self.id(), {'build': buildNumber})

    def set_tags(self, tags):
        sauceRest = SauceRest(self.username, self.accessKey)
        sauceRest.update(self.id(), {'tags': tags})

    def job_passed(self):
        sauceRest = SauceRest(self.username, self.accessKey)
        sauceRest.update(self.id(), {'passed': True})

    def job_failed(self):
        sauceRest = SauceRest(self.username, self.accessKey)
        sauceRest.update(self.id(), {'passed': False})

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
            startingUrl = "http://saucelabs.com"
        else:
            startingUrl = os.environ['SELENIUM_STARTING_URL']

        if 'SELENIUM_DRIVER' in os.environ and 'SELENIUM_HOST' in os.environ and 'SELENIUM_PORT' in os.environ:
            parse = ParseSauceURL(os.environ["SELENIUM_DRIVER"])
            driver = selenium(os.environ['SELENIUM_HOST'], os.environ['SELENIUM_PORT'], parse.toJSON(), startingUrl)
            driver.start()

            if parse.getMaxDuration() != 0:
                driver.set_timeout(parse.getMaxDuration())

            wrapper = Wrapper(driver, parse)
            wrapper.dump_session_id()
            return wrapper
        else:
            driver = selenium("localhost", 4444, "*firefox", startingUrl)
            driver.start()
            return driver

    def createWebDriver(self):
        """
         Uses a driver specified by the 'SELENIUM_DRIVER' system property or the environment variable,
         and run the test against the domain specified in 'SELENIUM_STARTING_URL' system property or the environment variable.
         If no variables exist, a local Selenium web driver is created.
        """

        if 'SELENIUM_STARTING_URL' not in os.environ:
            startingUrl = "http://saucelabs.com"
        else:
            startingUrl = os.environ['SELENIUM_STARTING_URL']

        if 'SELENIUM_DRIVER' in os.environ and 'SELENIUM_HOST' in os.environ and 'SELENIUM_PORT' in os.environ:
            parse = ParseSauceURL(os.environ["SELENIUM_DRIVER"])

            desired_capabilities = {}
            if parse.getBrowser() == 'android':
                desired_capabilities = webdriver.DesiredCapabilities.ANDROID
            elif parse.getBrowser() in ['googlechrome', 'chrome']:
                desired_capabilities = webdriver.DesiredCapabilities.CHROME
            elif parse.getBrowser() == 'firefox':
                desired_capabilities = webdriver.DesiredCapabilities.FIREFOX
            elif parse.getBrowser() == 'htmlunit':
                desired_capabilities = webdriver.DesiredCapabilities.HTMLUNIT
            elif parse.getBrowser() == 'iexplore':
                desired_capabilities = webdriver.DesiredCapabilities.INTERNETEXPLORER
            elif parse.getBrowser() == 'iphone':
                desired_capabilities = webdriver.DesiredCapabilities.IPHONE
            else:
                desired_capabilities = webdriver.DesiredCapabilities.FIREFOX

            desired_capabilities['version'] = parse.getBrowserVersion()

            if 'SELENIUM_PLATFORM' in os.environ:
                desired_capabilities['platform'] = os.environ['SELENIUM_PLATFORM']
            else:
            #work around for name issues in Selenium 2
                if 'Windows 2003' in parse.getOS():
                    desired_capabilities['platform'] = 'XP'
                elif 'Windows 2008' in parse.getOS():
                    desired_capabilities['platform'] = 'VISTA'
                elif 'Linux' in parse.getOS():
                    desired_capabilities['platform'] = 'LINUX'
                else:
                    desired_capabilities['platform'] = parse.getOS()

            desired_capabilities['name'] = parse.getJobName()

            command_executor = "http://%s:%s@%s:%s/wd/hub" % (parse.getUserName(), parse.getAccessKey(
            ), os.environ['SELENIUM_HOST'], os.environ['SELENIUM_PORT'])

            #make sure the test doesn't run forever if if the test crashes
            if parse.getMaxDuration() != 0:
                desired_capabilities['max-duration'] = parse.getMaxDuration()
                desired_capabilities['command-timeout'] = parse.getMaxDuration()

            if parse.getIdleTimeout() != 0:
                desired_capabilities['idle-timeout'] = parse.getIdleTimeout()

            if 'SELENIUM_DISABLE_POPUP_HANDLER' in os.environ:
                disable_popup_handler_flag = os.environ['SELENIUM_DISABLE_POPUP_HANDLER']
                if disable_popup_handler_flag.lower() == 'true' or disable_popup_handler_flag == '1':
                    desired_capabilities["disable-popup-handler"] = True

            driver = webdriver.Remote(desired_capabilities=desired_capabilities, command_executor=command_executor)
            driver.get(startingUrl)
            wrapper = Wrapper(driver, parse)
            wrapper.dump_session_id()
            return wrapper

        else:
            return webdriver.Firefox()
