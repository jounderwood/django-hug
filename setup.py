# Python 3.5+ setup using setup.cfg
from setuptools import setup
import os

from configparser import ConfigParser


PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

REQUIREMENTS_FILE = 'requirements.txt'
REQUIREMENTS = open(os.path.join(PROJECT_DIR, REQUIREMENTS_FILE)).readlines()

DEV_VERSION = os.environ.get('DEV_VERSION')
if DEV_VERSION:
    SETUP_CFG = os.path.join(PROJECT_DIR, 'setup.cfg')
    config = ConfigParser()
    config.read(SETUP_CFG)
    VERSION = config['metadata']['version']
    config['metadata']['version'] = '{}.dev{}'.format(VERSION, DEV_VERSION)
    with open(SETUP_CFG, 'w') as f:
        config.write(f)


setup(
    install_requires=REQUIREMENTS,
)
