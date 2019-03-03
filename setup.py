#! /usr/bin/python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
    name='endurance',
    version='0.1',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'pyyaml',
        'kubernetes',
        'openshift',
    ],
    entry_points='''
        [console_scripts]
        enduranceRunner=src.scale.runner:main     
    ''',
)
