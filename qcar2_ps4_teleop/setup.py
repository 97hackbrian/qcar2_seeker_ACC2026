import os
from glob import glob
from setuptools import find_packages, setup

package_name = 'qcar2_ps4_teleop'

setup(
    name=package_name,
    version='1.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        # Install launch files
        (os.path.join('share', package_name, 'launch'),
            glob(os.path.join('launch', '*launch.[pxy][yma]*'))),
        # Install config files
        (os.path.join('share', package_name, 'config'),
            glob(os.path.join('config', '*.yaml'))),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='QCar2 Developer',
    maintainer_email='user@qcar2.local',
    description='Control the QCar2 with a PS4 DualShock 4 controller via Bluetooth',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'ps4_teleop_node = qcar2_ps4_teleop.ps4_teleop_node:main',
            'control = qcar2_ps4_teleop.control:main',
            'try_joy = qcar2_ps4_teleop.try_joy:main',
        ],
    },
)
