#!/usr/bin/env python

""" 
Streply SDK - The all-in-one monitoring app for smart devs
"""

from setuptools import setup, find_packages
import os

# Odczytanie długiego opisu z README.md
with open('README.md', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='streply-sdk',
    version='1.0.0',
    author='Streply',
    author_email='support@streply.com',
    description='The all-in-one monitoring app for smart devs',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/streply/streply-python',
    project_urls={
        'Documentation': 'https://docs.streply.com/',
        'Changelog': 'https://streply.com/changelog',
        'Help & Support': 'https://streply.com/help',
    },
    packages=find_packages(),
    include_package_data=True,
    python_requires='>=3.6',
    install_requires=[
        'requests>=2.20.0',
        'urllib3>=1.20',
    ],
    extras_require={
        'django': [''],
        'flask': ['']
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: System :: Logging',
        'Topic :: System :: Monitoring',
    ],
)
