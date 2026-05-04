from setuptools import find_packages, setup

package_name = 'py_pubsub_aruco'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='ollylove',
    maintainer_email='olly.love@ontariotechu.net',
    description='pub sending image, sub reading image and detecting Aruco ID',
    license='Apache-2.0',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'talker = py_pubsub_aruco.publisher_member_function:main',
            'listener = py_pubsub_aruco.subscriber_member_function:main',
        ],
    },
)
