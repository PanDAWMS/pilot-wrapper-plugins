#!/usr/bin/env python 

import commands
import os

from base import Base
from wrapperutils import *


def printfile(filename):
    """
    in case filename it is like 
        source foo; source bar
    we:
        - split by ;
        - split by blank space and get the last item
    """

    filenames = filename.split(';') 
    for filename in filenames:
        filename = filename.split()[-1]
        _printfile(filename)

def _printfile(filename):
    print 
    print '---- printing file %s ----' %filename
    print '---- printing file STARTS ----'
    print commands.getoutput('cat %s' %filename) 
    print '---- printing file ENDS ----'
    print 


class atlasdebug(Base):
       
        def __init__(self, opts):
     
                super(atlasdebug,self).__init__(opts) 
                self.log.info('Base: Object initialized.')
     
        # =========================================================== 
        #                      PRE-PROCESS 
        # =========================================================== 
 
        def pre_run(self):

                self.log.debug('pre_run: Starting.')

                self._testproxy()
                self._setupcctools()
                self._setpybin()
                self._envvars()
                self._setupWN()
                self._setxpython()
                self._schedconfigsetup()

                super(atlasdebug, self).pre_run()

                self.log.debug('pre_run: Leaving.')
        
        def _downloadtarball(self):
        
                self.log.debug('downloadtarball: Starting.')

                libcode = self.opts.pilotcode
                script = self._getScript(libcode)
                filename = script+'.tar.gz'
       
                pilotsrcurls = self.opts.pilotcodeurl.split(',')
                for url in pilotsrcurls:
                        st, out = self.tarball.download(url, filename)                
                        if st == 0:
                               break
                else:
                       self.log.warning('download: failed to download %s' % filename)

                self.log.debug('downloadtarball: Leaving.')
        
        def _getScript(self, libcode):
                '''
                get a script to be run from the libcode input option.
                If libcode has only one item, that is picked up.
                If libcode has two items, the first one is selected
                with a probability of 99%, and the second one 1% of times.
                '''
        
                self.log.debug('_getScript: Starting.')

                scripts = libcode.split(',')
                if len(scripts) == 1:
                        script_index = 0
                elif len(scripts) == 2:
                        # select randomly one of the two scripts
                        # with a probability of 99% to pick up the first one
                        weights = [
                                (1, 0.01),
                                (0, 0.99)
                        ]
                        script_index = getScriptIndex(weights)
                else:
                        self.log.warning("_getScript: Current weight function only handles two libcode scripts")
                        script_index = 0
                self.log.info('_getScript: got script index %s' %script_index)

                s = scripts[script_index]
                self.log.info('_getScript: downloading script %s' %s)

                self.log.debug('_getScript: Leaving.')
                return s
        
        def _envvars(self):

                self.log.debug('_envvars: Starting.')
                self._envvarspanda()
                self._envvarsdq2()
                self.log.debug('_envvars: Leaving.')

        def _envvarspanda(self):
                os.environ['PANDA_URL'] = 'http://pandaserver.cern.ch:25085/server/panda'
                os.environ['PANDA_URL_SSL'] = 'https://pandaserver.cern.ch:25443/server/panda'

        def _envvarsdq2(self):
                os.environ['DQ2_URL_SERVER'] = 'http://atlddmcat.cern.ch/dq2/'
                os.environ['DQ2_URL_SERVER_SSL'] = 'https://atlddmcat.cern.ch:443/dq2/'

        def _setpybin(self):
                '''
                set variable pybin
                '''
                self.pybin = ''
                st, out = commands.getstatusoutput('which python32 2> /dev/null')
                if st == 0:
                        self.log.info('_setpybin: python32 found in %s' %out)
                        self.pybin = out
                else:
                        st, out = commands.getstatusoutput('which python 2> /dev/null')
                        self.pybin = out
        
        def _setxpython(self):
                '''
                set variable pybin
                '''
                if not self.pybin:
                        self.xpython = commands.getoutput('which python')
                        self.pybin = self.xpython
                else:
                        self.xpython = self.pybin

                if os.path.exists(self.xpython):
                        self.log.info('_setxpython: python found: %s' %self.xpython)
                        version = commands.getoutput('%s -V 2>&1' %self.xpython)
                        self.log.info('_setxpython: python version is %s' %version)
                else:
                        st, out = commands.getstatusoutput('which %s' %self.xpython)
                        if st == 0:
                                self.pybin = out
                                self.log.info('_setxpython: python found: %s' %self.pybin)
                                version = commands.getoutput('%s -V 2>&1' %self.pybin)
                                self.log.info('_setxpython: python version is %s' %version)
                        else:
                                self.log.error('_setxpython: python not found. Cannot continue') 
                                # FIXME !! here I should stop !!
                
        def _setupcctools(self):
                '''
                source CCTOOLS
                '''

                self.log.debug('_setupcctools: Starting.')

                OSG_APP = os.environ.get('OSG_APP', '')
        
                if OSG_APP == '':
                        self.log.info('_setupcctools: Environment variable OSG_APP not defined')
                else:
                        setuppath = '%s/atlas_app/atlas_rel/cctools/latest/setup.sh' %OSG_APP
                        if os.path.isfile(setuppath):
                                cmd = 'source %s' %setuppath
                                self.log.info('_setupcctools: Running CCTOOLS setup with command: %s' %cmd)
                                source(cmd)
                                printfile(setuppath)

                        else:
                                self.log.info('_setupcctools: CCTOOLS setup file does not exist. Cannot be sourced.')

                self._displayenv('_setupcctools')
                
                self.log.debug('_setupcctools: Leaving.')
        
        def _setupWN(self):
                ''' 
                source the WNCLIENT if available (necessary for using LFC in OSG)
                ''' 
        
                self.log.debug('_setupWN: Starting.')

                OSG_APP = os.environ.get('OSG_APP', '')
        
                if OSG_APP == '':
                        self.log.info('_setupWN: Environment variable OSG_APP not defined')
                else:
                        setuppath = '%s/atlas_app/atlaswn/setup.sh' %OSG_APP
                        if os.path.isfile(setuppath):
                                cmd = 'source %s' %setuppath
                                self.log.info('_setupWN: Running WNCLIENT setup with command: %s' %cmd)
                                source(cmd)
                                printfile(setuppath)
                                self._displayenv('_setupWN')
                        else:
                                self.log.info('_setupWN: OSG_APP defined but WNCLIENT setup file %s does not exist' %setuppath)
        
                        setuppath = '%s/atlas_app/atlas_rel/local/setup.sh' %OSG_APP
                        if os.path.isfile(setuppath):
                                cmd = 'source %s' %setuppath
                                self.log.info('_setupWN: sourcing command: %s' %cmd)
                                source(cmd)
                                printfile(setuppath)
                                self._displayenv('_setupWN')
                        else:
                                self.log.info('_setupWN: OSG_APP defined but WNCLIENT setup file %s does not exist' %setuppath)

                self._displayenv('_setupWN')

                self.log.debug('_setupWN: Leaving.')
       

        def _schedconfigsetup(self):
                '''
                special setup commands to be performed just after
                sourcing the grid environment, 
                but before doing anything else
                following instructions from SchedConfig
                '''
        
                self.log.debug('_schedconfigsetup: checking schedconfig for specific setup commands')
        
                cmd = 'curl  --connect-timeout 20 --max-time 60 "http://panda.cern.ch:25880/server/pandamon/query?tpmes=pilotpars&getpar=envsetup&queue=%s" -s -S' %self.opts.batchqueue
                self.log.debug('_schedconfigsetup: curl command is %s' %cmd)
                out = commands.getoutput(cmd)
                if out == "":
                        self.log.info('_schedconfigsetup: output of curl command was empty. Leaving')
                        return
                if out[:13] == 'No data found':
                        self.log.info('_schedconfigsetup: output of curl command was "No data found". Leaving')
                        return
                # else... 
                self.log.info('_schedconfigsetup: command found is %s' %out)
                source(out)
                printfile(out)
        
                self._displayenv('_schedconfigsetup')
        
                self.log.debug('_schedconfigsetup: Leaving')

 
        # =========================================================== 
        #                      RUN 
        # =========================================================== 

        def run(self):
                self.log.debug('run: Starting.')

                pilotopts = ' --pilotpars=\\\"%s\\\"' %self.opts.extraopts
                cmd = './atlasProdPilot.py --site=%s --queue=%s %s'  %(self.opts.wmsqueue, self.opts.batchqueue, pilotopts)
                if self.pybin:
                        cmd = '%s %s' %(self.pybin, cmd)
                self.log.debug('run: command is %s' %cmd)

###                if self.opts.mode.lower() == 'test':
###                        self.log.info('run: Testing mode, not performing any operation') 
###                else:
###                        self._run(cmd)

                self.log.debug('run: Leaving.')

###        def _run(self, cmd):
###
###                self.log.debug('_run: Starting.')
###
###                # touch job.out
###                open('job.out', 'w').close()
###                st, out = commands.getstatusoutput(cmd)
###                self.log.debug('_run: status of command execution is %s' %st)
###                self.log.debug('_run: output of command execution is %s' %out)
###                print commands.getoutput('cat ./job.out')
###        
###                if st == 2:
###                        self.log.warning('!!FINISHED!!0!!site offline')
###                elif st != 0:
###                        self.log.warning('!!FAILED!!2007!!%s script failed' %self.opts.pilotcode)
###
###                self.log.debug('_run: Exiting at %s. return value %s' %(time.ctime(),st))

        # =========================================================== 
        #                      POST-PROCESS 
        # =========================================================== 

        def post_run(self):
                super(atlasdebug, self).post_run()

