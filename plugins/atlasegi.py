#!/usr/bin/env python 

import commands
import getopt
import os
import time

from base import Base
from atlas import atlas
import wrapperutils as utils
import wrapperexceptions as wexceptions


try:
    import json as json
except ImportError, err:
    import simplejson as json



class atlasegi(atlas):
       
        def __init__(self, opts):
     
                super(atlasegi,self).__init__(opts) 
                self.log.info('atlasegi: Object initialized.')

        # =========================================================== 
        #                      PRE-PROCESS 
        # =========================================================== 
           

        def pre_run(self):

                self.log.debug('pre_run: Starting.')
                super(atlasegi,self).pre_run() 
                self.log.debug('pre_run: Leaving.')
                return 0  # FIXME: check every step
        

        # =========================================================== 
        #                      RUN 
        # =========================================================== 

        def run(self):

                self.log.debug('run: Starting.')
                super(atlasegi,self).run() 
                self.log.debug('run: Leaving.')
                return self.rc 

        # =========================================================== 
        #                      POST-PROCESS 
        # =========================================================== 


        def post_run(self):
                self.log.debug('post_run: Starting.')
                super(atlasegi,self).post_run() 
                self.log.debug('post_run: Leaving.')
                return 0  # FIXME!! check every step !! 
