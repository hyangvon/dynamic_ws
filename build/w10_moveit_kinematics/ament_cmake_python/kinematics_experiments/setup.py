from setuptools import find_packages
from setuptools import setup

setup(
    name='kinematics_experiments',
    version='0.1.0',
    packages=find_packages(
        include=('kinematics_experiments', 'kinematics_experiments.*')),
)
