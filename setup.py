#!/usr/bin/env python

""" Official Streply SDK for Python """

from setuptools import setup, find_packages
import os

here = os.path.abspath(os.path.dirname(__file__))

def read_file(file_name):
    with open(os.path.join(here, file_name)) as in_file:
        return in_file.read()

setup(
    name='streply-sdk',
    version='0.0.01',
    author='Streply',
    author_email='support@streply.com',
    project_urls={
        "Documentation": "https://docs.streply.com/",
        "Changelog": "https://streply.com/changelog",
        "Help & Support": "https://streply.com/help",
    },
    description='The all-in-one monitoring app for smart devs (https://streply.com)',
    long_description=read_file("README.md"),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    classifiers=[
        "Environment :: Web Environment",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires='>=3',
)
