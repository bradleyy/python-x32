#!/usr/bin/env python

from distutils.core import setup

setup(name='x32',
      version='1.0',
      description='Python script to use passive OSC-clients with X32',
      author='tjoracoder',
      author_email='',
      url='',
      scripts=['bin/x32.py', 'bin/x32-mirror.py', 'bin/x32-osc-proxy.py', 'bin/x32parameters.py', 'bin/dumpmessages.py'],
      packages=['osc'],
      )
