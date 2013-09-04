from distutils.core import setup

setup(
    name='SeleniumFactory-for-Python',
    version='0.3',
    packages=['selenium_factory'],
    package_dir={'selenium_factory': 'src/selenium_factory'},
    url='https://github.com/mattfair/SeleniumFactory-for-Python',
    license='',
    author='Matt Fair',
    author_email='matt.fair@gmail.com',
    description='Simple interface factory to create Selenium objects to run at SauceLabs', requires=['selenium']
)
