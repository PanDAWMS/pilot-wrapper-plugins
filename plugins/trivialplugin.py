#!/usr/bin/env python 


import commands
from base import Base
import wrapperexceptions as exceptions

class trivial(Base):
        '''
        in this case, what we need is exactly the content of class Base
        '''

        def __init__(self, opts):
       
                super(trivial,self).__init__(opts) 
                self.log.info('Base: Object initialized.')
        
        # =========================================================== 
        #                       PRE-RUN 
        # =========================================================== 

        def pre_run(self):

                self.log.debug('pre_run at trivial: Starting')
                rc = super(trivial, self).pre_run()
                self.log.debug('pre_run at trivial: Leaving')
                return rc
                
        
#        def _downloadtarball(self):
#       
#                filename = self.opts.pilotcode + '.tar.gz'
#
#                if not self.opts.pilotcodeurl:
#                        # if variable pilotcodeurl has no value...
#                        self.log.critical('download: self.opts.pilotcodeurl has no value. Raising exception.')
#                        raise exceptions.WrapperException('self.opts.pilotcodeurl has no value.')
#                 
#                self.tarball.download(self.opts.pilotcodeurl, filename)

        def _downloadtarball(self):
       
                filename = self.opts.pilotcode

                if not self.opts.pilotcodeurl:
                        # if variable pilotcodeurl has no value...
                        self.log.critical('download: self.opts.pilotcodeurl has no value. Raising exception.')
                        raise exceptions.WrapperException('self.opts.pilotcodeurl has no value.')
                 
                self.tarball.download(self.opts.pilotcodeurl, filename)

        def _untar(self):
                pass

        def _removetarball(self):
                pass


        # =========================================================== 
        #                       RUN
        # =========================================================== 

        def run(self):

                self.log.debug('run at trivial: Starting')
                err, out =  commands.getstatusoutput('chmod +x %s; ./%s %s' %(self.opts.pilotcode, self.opts.pilotcode, self.opts.extraopts) )
                self.rc = err
                print out
                self.log.debug('run at trivial: Leaving')
        
        # =========================================================== 
        #                       POST-RUN 
        # =========================================================== 

        def post_run(self):

                self.log.debug('post_run at trivial: Starting')
                super(trivial, self).post_run()
                self.log.debug('post_run at trivial: Leaving')

        def _exit(self):
                pass
