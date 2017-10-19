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



class atlasosg(atlas):
       
        def __init__(self, opts):
     
                super(atlasosg,self).__init__(opts) 
                self.log.info('atlasosg: Object initialized.')

        # =========================================================== 
        #                      PRE-PROCESS 
        # =========================================================== 
           

        def pre_run(self):

                self.log.debug('pre_run: Starting.')
                super(atlasosg,self).pre_run() 

                # FIXME: ?? should it be an exception instead of an RC ??
                rc = self._setupWN()
                if rc != 0:
                    self.log.critical('something went wrong with setupWN. Aborting.')
                    return rc

                # FIXME: ?? should it be an exception instead of an RC ??
                rc = self._setupatlas()
                if rc != 0:
                    self.log.critical('something went wrong with atlas setup. Aborting.')
                    return rc

                # FIXME: ?? should it be an exception instead of an RC ??
                rc = self._schedconfigsetup()   # apparently can not be removed yet, analysis jobs fail
                if rc != 0:
                    self.log.critical('something went wrong with _schedconfigsetup. Aborting.')
                    return rc

                # TEMPORARY, to test sourcing rucio
                rc = self._setuprucio() 
                if rc != 0:
                    self.log.critical('something went wrong with _setuprucio. Aborting.')
                    return rc

                self.log.debug('pre_run: Leaving.')
                return 0  # FIXME: check every step
        
        def _downloadtarball(self):
        
                self.log.debug('downloadtarball: Starting.')

                libcode = self.opts.pilotcode
                script = self._getScript(libcode)
                filename = script+'.tar.gz'

                if not self.opts.pilotcodeurl:
                        # if variable pilotcodeurl has no value...
                        self.log.critical('download: self.opts.pilotcodeurl has no value. Raising exception.')
                        raise wexceptions.WrapperException('self.opts.pilotcodeurl has no value.')
        
                pilotsrcurls = self.opts.pilotcodeurl.split(',')
                for url in pilotsrcurls:
                        self.tarball = utils.Tarball(url, filename)
                        st, out = self.tarball.download()                
                        if st == 0:
                               break
                else:
                        # if all URLs failed and no tarball was downloaded...
                        self.log.critical('download: failed to download %s. Raising exception.' % filename)
                        raise wexceptions.WrapperException('failed to download VO tarball %s' %filename)

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
                        script_index = utils.getScriptIndex(weights)
                else:
                        self.log.warning("_getScript: Current weight function only handles two libcode scripts")
                        script_index = 0
                self.log.info('_getScript: got script index %s' %script_index)

                s = scripts[script_index]
                self.log.info('_getScript: downloading script %s' %s)

                self.log.debug('_getScript: Leaving.')
                return s

        def _untar(self):
                self.tarball.untar()

        
        def _setupWN(self):
                ''' 
                source the WNCLIENT if available (necessary for using LFC in OSG)
                ''' 
        
                self.log.debug('_setupWN: Starting.')
                OSG_APP = os.environ.get('OSG_APP', '')
        
                if OSG_APP == '':
                    self.log.info('_setupWN: Environment variable OSG_APP not defined')
                    return 1
                else:
                    setuppath = '%s/atlas_app/atlaswn/setup.sh' %OSG_APP
                    if not os.path.isfile(setuppath):
                        self.log.info('_setupWN: OSG_APP defined but WNCLIENT setup file %s does not exist' %setuppath)
                        return 0 # FIXME ?? is returning 0 correct ??
                    else:
                        cmd = 'source %s' %setuppath
                        self.log.info('_setupWN: Running WNCLIENT setup with command: %s' %cmd)
                        rc, out = self.source(cmd)
                        self.log.debug('_setupWN: rc, output of sourcing cmd %s:\n%s\n%s' %(cmd, rc, out))
                        utils._displayenv('atlaswn')
                        utils._printsyspath('atlaswn')

                self.log.debug('_setupWN: Leaving.')
                return rc

        
        def _setupatlas(self):
                ''' 
                source the local/setup.sh global ATLAS setup file
                ''' 

                self.log.debug('_setupatlas: Starting.')
                OSG_APP = os.environ.get('OSG_APP', '')

                if OSG_APP == '':
                    self.log.info('_setupatlas: Environment variable OSG_APP not defined')
                    return 1
                else:
                    setuppath = '%s/atlas_app/atlas_rel/local/setup.sh' %OSG_APP
                    if not os.path.isfile(setuppath):
                        self.log.info('setupatlas: OSG_APP defined but setup file %s does not exist' %setuppath)
                        raise wexceptions.WrapperExceptionSource(setuppath)
                    else:
                        cmd = 'source %s -s %s' %(setuppath, self.opts.wmsqueue)
                        self.log.info('_setupatlas: sourcing command: %s' %cmd)
                        rc, out = self.source(cmd)
                        self.log.debug('_setupatlas: rc, output of sourcing cmd %s:\n%s\n%s' %(cmd, rc, out))
                        utils._displayenv('local/setup.sh')
                        utils._printsyspath('local/setup.sh')

                self.log.debug('_setupatlas: Leaving.')
                return rc


        def _schedconfigsetup(self):
                '''
                special setup commands to be performed just after
                sourcing the grid environment, 
                but before doing anything else
                following instructions from SchedConfig
                '''
        
                self.log.debug('_schedconfigsetup: checking schedconfig for specific setup commands')
                cmd = 'curl --connect-timeout 20 --max-time 120 -sS "http://pandaserver.cern.ch:25085/cache/schedconfig/%s.pilot.json"' %self.opts.batchqueue
                self.log.debug('_schedconfigsetup: curl command is %s' %cmd) 

                ntrials = 3
                for i in range(ntrials):

                    self.log.info('_schedconfigsetup: trial %s for command %s' %(i+1, cmd))
                    rc, out = commands.getstatusoutput(cmd)
                    # out is json format. With json.load() we will convert it into a dictionary    
                    if rc == 0:
                        self.log.debug('content of schedconfig is %s' %out)
                        schedconfigcmd = json.loads(out)['envsetup']
                        if not schedconfigcmd:
                                self.log.warning('_schedconfigsetup: variable envsetup from schedconfig was empty. Leaving')
                                return 0
                        # else... 
                        self.log.info('_schedconfigsetup: command found is %s' %schedconfigcmd)
                        rc, out = self.source(schedconfigcmd)
                        self.log.debug('_schedconfigsetup: rc, output of sourcing cmd %s:\n%s\n%s' %(schedconfigcmd, rc, out))
        
                        utils._displayenv('schedconfigsetup')
                        utils._printsyspath('schedconfigsetup')

                        break

                    else:

                        import socket
                        hostname = socket.gethostname()
                        err, ipinfo = commands.getstatusoutput('ifconfig | grep Bcast')
                        if err==0:
                            self.log.error('download: command to download schedconfig: %s failed at trial %s at hostname %s with IP %s with RC=%s and message=%s' %(cmd, i+1, hostname, ipinfo, rc, out))
                        else:
                            self.log.error('download: command to download schedconfig: %s failed at trial %s at hostname %s with RC=%s and message=%s' %(cmd, i+1, hostname, rc, out))

                        time.sleep(10)

                # If all 3 trials failed...
                else:
                    self.log.critical('download: command to download schedconfig: %s failed. Aborting. ' %cmd)
                    return 1
        
                self.log.debug('_schedconfigsetup: Leaving')
                return 0




        ### BEGIN TEST ###
        # setup rucio in the new way 
        def _setuprucio(self):

            self.log.debug('_setuprucio: Starting.')
    
            basedir = os.environ['ATLAS_LOCAL_ROOT_BASE']
            setuppath = os.path.join(basedir, 'x86_64/rucio-clients/current/setup.sh')

            # first, lets check if rucio is already set
            # we just try to import it
            try:
                import rucio
                self.log.info('_setuprucio: rucio is already import-able. Doing nothing else.')
                self.log.info('_setuprucio: location of rucio package is %s' %rucio.__file__)
                return 0
            except:
                self.log.info('_setuprucio: failed to import rucio. Sourcing lsetup')
                cmd = 'source %s -s %s' %(setuppath, self.opts.wmsqueue)
                self.log.info('_setuprucio: sourcing command: %s' %cmd)
                ###rc, out = self.source(cmd)
                rc, out = utils.source(cmd)
                self.log.debug('_setuprucio: rc, output of sourcing cmd %s:\n%s\n%s' %(cmd, rc, out))
                utils._displayenv('_ruciosetup')
                utils._printsyspath('_ruciosetup')
    
                self.log.debug('_setuprucio: Leaving.')
                return rc
        ### BEGIN TEST ###
        


        
        # =========================================================== 
        #                      RUN 
        # =========================================================== 

        def run(self):

                self.log.debug('run: Starting.')
                super(atlasosg,self).run() 
                self.log.debug('run: Leaving.')
                return self.rc 

        # =========================================================== 
        #                      POST-PROCESS 
        # =========================================================== 


        def post_run(self):
                self.log.debug('post_run: Starting.')
                super(atlasosg,self).post_run() 
                self.log.debug('post_run: Leaving.')
                return 0  # FIXME!! check every step !! 
