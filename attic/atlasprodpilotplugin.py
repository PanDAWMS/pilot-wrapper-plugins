#!/usr/bin/env python 

import commands
import getopt
import os
import time

from base import Base
import wrapperutils as utils
import wrapperexceptions as exceptions


class atlasprodpilot(Base):
       
        def __init__(self, opts):
     

                super(atlasprodpilot,self).__init__(opts) 
                self.log.info('Base: Object initialized.')

                self.source = utils.source()
    
     
        # =========================================================== 
        #                      PRE-PROCESS 
        # =========================================================== 
 
        def pre_run(self):

                self.log.debug('pre_run: Starting.')

                ### BEGIN TEST 0.9.13 ####
                #self._testproxy()
                utils._testproxy()
                ### END TEST 0.9.13 ####

                self._setupcctools()
                self._setupWN()
                rc = self._schedconfigsetup()   # apparently can not be removed yet, analysis jobs fail
                if rc != 0:
                    # something went wrong
                    return rc

                super(atlasprodpilot, self).pre_run()

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
                        raise exceptions.WrapperException('self.opts.pilotcodeurl has no value.')
        
                pilotsrcurls = self.opts.pilotcodeurl.split(',')
                for url in pilotsrcurls:
                        ### BEGIN TEST 0.9.13 ###
                        #st, out = self.tarball.download(url, filename)                
                        self.tarball = utils.Tarball(url, filename)
                        st, out = self.tarball.download()                
                        ### END TEST 0.9.13 ###
                        if st == 0:
                               break
                else:
                        # if all URLs failed and no tarball was downloaded...
                        self.log.critical('download: failed to download %s. Raising exception.' % filename)
                        raise exceptions.WrapperException('failed to download VO tarball %s' %filename)

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
                                out = self.source(cmd)
                                self.log.debug('_setupcctools: output of sourcing cmd %s plus resulting environment and new sys.path :\n%s' %(cmd, out))

                        else:
                                self.log.info('_setupcctools: CCTOOLS setup file does not exist. Cannot be sourced.')

                ### BEGIN TEST 0.9.13 ###
                #self._displayenv('_setupcctools')
                utils._displayenv('_setupcctools')
                ### END TEST 0.9.13 ###
                
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
                                out = self.source(cmd)
                                self.log.debug('_setupWN: output of sourcing cmd %s plus resulting environment and new sys.path :\n%s' %(cmd, out))

                        else:
                                self.log.info('_setupWN: OSG_APP defined but WNCLIENT setup file %s does not exist' %setuppath)
        
                        setuppath = '%s/atlas_app/atlas_rel/local/setup.sh' %OSG_APP
                        if os.path.isfile(setuppath):
                                cmd = 'source %s -s %s' %(setuppath, self.opts.wmsqueue)
                                self.log.info('_setupWN: sourcing command: %s' %cmd)
                                out = self.source(cmd)
                                self.log.debug('_setupWN: output of sourcing cmd %s plus resulting environment and new sys.path:\n%s' %(cmd, out))

                        else:
                                self.log.info('_setupWN: OSG_APP defined but WNCLIENT setup file %s does not exist' %setuppath)

                ### BEGIN TEST 0.9.13 ###
                #self._displayenv('_setupWN')
                utils._displayenv('_setupWN')
                ### END TEST 0.9.13 ###

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

                ntrials = 3
                for i in range(ntrials):

                    self.log.info('_schedconfigsetup: trial %s for command %s' %(i+1, cmd))
                    rc, out = commands.getstatusoutput(cmd)
                    if rc == 0:
                        schedconfigcmd = out
                        if schedconfigcmd == "":
                                self.log.warning('_schedconfigsetup: output of curl command was empty. Leaving')
                                return 0
                        if schedconfigcmd[:13] == 'No data found':
                                self.log.warning('_schedconfigsetup: output of curl command was "No data found". Leaving')
                                return 0
                        # else... 
                        self.log.info('_schedconfigsetup: command found is %s' %schedconfigcmd)
                        out = self.source(schedconfigcmd)
                        self.log.debug('_schedconfigsetup: output of sourcing cmd %s plus resulting environment and new sys.path :\n%s' %(schedconfigcmd, out))
        
                        ### BEGIN TEST 0.9.13 ###
                        #self._displayenv('_schedconfigsetup')
                        utils._displayenv('_schedconfigsetup')
                        ### END TEST 0.9.13 ###

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
        
        # =========================================================== 
        #                      RUN 
        # =========================================================== 

        def run(self):

                self.log.debug('run: Starting.')

                pilotargs = self._pilotargs()
                self.log.debug('run: pilot args are = %s' %pilotargs)

                # import and invoke the ATLAS pilot code
                import pilot
                self.rc = pilot.runMain(pilotargs)

                rc_msg = {
                    64: "Site offline",
                    65: "General pilot error, consult batch log",
                    66: "Could not create directory",
                    67: "No such file or directory",
                    68: "Voms proxy not valid",
                    69: "No space left on local disk",
                    70: "Exception caught by pilot",
                    71: "Pilot could not download queuedata",
                    72: "Pilot found non-valid queuedata",
                    73: "Software directory does not exist",
                    137: "General kill signal", # Job terminated by unknown kill signal
                    143: "Job killed by signal: SIGTERM", # 128+15           
                    131: "Job killed by signal: SIGQUIT", # 128+3            
                    139: "Job killed by signal: SIGSEGV", # 128+11           
                    158: "Job killed by signal: SIGXCPU", # 128+30           
                    144: "Job killed by signal: SIGUSR1", # 128+16           
                    138: "Job killed by signal: SIGBUS"   # 128+10           
                }
                msg = rc_msg.get(self.rc, "")
                if msg:
                    msg = "(%s)" %msg
               
                self.log.info('run: pilot returned rc=%s %s' %(self.rc, msg))

                self.log.debug('run: Leaving.')
                return self.rc 

        def _pilotargs(self):
                """
                prepares the list of input arguments for pilot.py
                """

                self.log.debug('Starting.')

                ###extraopts = self.opts.extraopts.split()
                extraopts = self.opts.extraopts


                #### add -s and -h to extraopts
                if ' -s ' not in extraopts:
                        self.log.info('Adding "-s %s" to pilotargs' %self.opts.wmsqueue)
                        extraopts += ' -s %s' %self.opts.wmsqueue
                if ' -h ' not in extraopts:
                        self.log.info('Adding "-h %s" to pilotargs' %self.opts.batchqueue)
                        extraopts += ' -h %s' %self.opts.batchqueue



                # check if -d is in extraopts
                # if not, we use the value of $OSG_WN_TMP if defined (or $TMP otherwise)
                wndir = None 
                if ' -d ' not in extraopts:
                        if 'OSG_WN_TMP' in os.environ.keys():
                                wndir = os.environ['OSG_WN_TMP']
                                self.log.info('Adding as value for -d $OSG_WN_TMP=%s.' %wndir)
                        else:
                                wndir = os.environ['TMP']
                                self.log.info('Adding as value for -d $TMP=%s.' %wndir)

                if wndir:
                        extraopts += " -d %s" %wndir

                # Finally we convert the string into a list
                pilotargs = extraopts.split()
                self.log.debug('Leaving with list %s.' %pilotargs)
                return pilotargs 

            


        # =========================================================== 
        #                      POST-PROCESS 
        # =========================================================== 

        def post_run(self):
                super(atlasprodpilot, self).post_run()
                return 0 # FIXME, return what super().post_run() returns

