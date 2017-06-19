#!/usr/bin/env python 

from base import Base

class null(Base):
        '''
        this class does not do anything at all.
        It is just for testing purposes, in case we need
        to test the wrappers but not interested in 
        running any actual payload. 
        '''
        def execute(self):
                print 'Null Wrapper called'
