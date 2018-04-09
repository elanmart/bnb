from os import path

from setuptools import find_packages, setup

_HERE = path.abspath(path.dirname(__file__))

with open(path.join(_HERE, 'README.md')) as f:
    LONG_DESCRIPTION = f.read()

setup(
    name='bnb',
    version='0.1.0',
    description='My own Barnabe-Basile to manage machine learning workflows',
    LONG_DESCRIPTION=LONG_DESCRIPTION,
    url='',
    author='Marcin Elantkowski',
    author_email='marcin.elantkowski@gmail.com',
    license='MIT',
    keywords='',
    packages=find_packages(exclude=['aws', 'examples', 'test']),
    install_requires=[
        # dispatch
        'dill',
        # tracker,
        'tinydb',
        'gitpython',
        # misc,
        'wrapt',
        'attrs',
    ],
    package_data={},
    entry_points={
        'console_scripts': [
            'bump=bnb.entrypoints:bump',
            'v=bnb.entrypoints:print_version'
        ],
    },
)
