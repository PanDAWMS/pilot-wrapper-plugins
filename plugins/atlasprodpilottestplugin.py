#!/usr/bin/env python 

import commands
import getopt
import os
import time

from base import Base
import wrapperutils as utils
import wrapperexceptions as exceptions


class atlasprodpilottest(Base):
       
        def __init__(self, opts):
     

                super(atlasprodpilottest,self).__init__(opts) 
                self.log.info('Base: Object initialized.')

                self.source = utils.source()
    
     
        # =========================================================== 
        #                      PRE-PROCESS 
        # =========================================================== 
 
        def pre_run(self):

                self.log.debug('pre_run: Starting.')

                self._testproxy()
                self._setupcctools()
                self._setupWN()
                rc = self._schedconfigsetup()   # apparently can not be removed yet, analysis jobs fail
                if rc != 0:
                    # something went wrong
                    return rc

                super(atlasprodpilottest, self).pre_run()

                self.log.debug('pre_run: Leaving.')
                return 0  # FIXME: check every step
        
        def _downloadtarball(self):
        
                self.log.debug('downloadtarball: Starting.')

                libcode = self.opts.pilotcode
                
                filename = libcode  #FIXME: this is legacy

                if not self.opts.pilotcodeurl:
                        # if variable pilotcodeurl has no value...
                        self.log.critical('download: self.opts.pilotcodeurl has no value. Raising exception.')
                        raise exceptions.WrapperException('self.opts.pilotcodeurl has no value.')
        
                pilotsrcurls = self.opts.pilotcodeurl.split(',')
                for url in pilotsrcurls:
                        st, out = self.tarball.download(url, filename) # FIXME: it is not really a tarball... 
                        if st == 0:
                               break
                else:
                        # if all URLs failed and no tarball was downloaded...
                        self.log.critical('download: failed to download %s. Raising exception.' % filename)
                        raise exceptions.WrapperException('failed to download VO tarball %s' %filename)

                # FIXME ???? Is this needed
                commands.getoutput('chmod +x ./%s' %libcode)


                self.log.debug('downloadtarball: Leaving.')

        def _untar(self):
                # FIXME : maybe temporary solution
                pass

        def _removetarball(self):
                # FIXME : maybe temporary solution
                pass

        
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
                                self.log.debug('_setupcctools: output of sourcing cmd %s plus resulting environment:\n%s' %(cmd, out))

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
                                out = self.source(cmd)
                                self.log.debug('_setupWN: output of sourcing cmd %s plus resulting environment:\n%s' %(cmd, out))

                        else:
                                self.log.info('_setupWN: OSG_APP defined but WNCLIENT setup file %s does not exist' %setuppath)
        
                        setuppath = '%s/atlas_app/atlas_rel/local/setup.sh' %OSG_APP
                        if os.path.isfile(setuppath):
                                cmd = 'source %s' %setuppath
                                self.log.info('_setupWN: sourcing command: %s' %cmd)
                                out = self.source(cmd)
                                self.log.debug('_setupWN: output of sourcing cmd %s plus resulting environment:\n%s' %(cmd, out))

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
                        self.log.debug('_schedconfigsetup: output of sourcing cmd %s plus resulting environment:\n%s' %(schedconfigcmd, out))
        
                        self._displayenv('_schedconfigsetup')

                        break

                    else:

                        import socket
                        hostname = socket.gethostname()
                        st, ipinfo = commands.getstatusoutput('ifconfig | grep Bcast')
                        if st==0:
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

                scriptargs = pilotargs = self._pilotargs()
                self.log.debug('run: script args are = %s' %scriptargs)

                cmd = './%s %s' %(self.opts.pilotcode, scriptargs)
                self.log.info('running testing command %s' %cmd)
                st, out = commands.getstatusoutput(cmd)  
                self.log.info('st and out of testing = %s, %s' %(st, out))

                self.rc = st
            
                self.log.debug('run: Leaving.')
                return self.rc 

        def _pilotargs(self):
                """
                prepares the list of input arguments for the script
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
                ###pilotargs = extraopts.split()
                pilotargs = extraopts

                self.log.debug('Leaving with list %s.' %pilotargs)
                return pilotargs



        # =========================================================== 
        #                      POST-PROCESS 
        # =========================================================== 

        def post_run(self):
                super(atlasprodpilottest, self).post_run()
                return 0 # FIXME: return whatever super().post_run()

