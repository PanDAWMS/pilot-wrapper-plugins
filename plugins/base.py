#!/usr/bin/env python 

import os
import commands
import logging

import wrapperutils as utils

class Base(object):
        """
        this class basically acts as an interface for the plugins.
        The API is method execute( )
        wich calls, in this order, methods
            -- pre_run()
            -- run()
            -- post_run()
        which must be implemented by each plugin.
        """

        def __init__(self, opts):

                self.log = logging.getLogger('wrapper.base')
                self.opts = opts
                self.rc = 0
                self.log.info('Base: Object initialized.')

        def execute(self):
                '''
                list of all steps to perform operations.
                The idea is to split tasks in atomic units
                that can be overriden one by one, when needed.
                '''

                self.log.debug('execute: Starting.')

                self.rc = self.pre_run()
                if self.rc != 0:
                    self.log.critical('execute: pre_run() failed with RC=%s. Aborting.' %self.rc)
                    return self.rc

                self.rc = self.run()
                if self.rc != 0:
                    self.log.error('execute: run() failed with RC=%s.' %self.rc)
                    return self.rc

                self.rc = self.post_run()
                if self.rc != 0:
                    self.log.error('execute: post_run() failed with RC=%s.' %self.rc)
                    return self.rc

                return 0

        def pre_run(self):
            raise NotImplementedError

        def run(self):
            raise NotImplementedError

        def post_run(self):
            raise NotImplementedError


