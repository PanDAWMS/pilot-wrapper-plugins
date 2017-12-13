#!/usr/bin/env python 

import commands
import getopt
import json
import os
import subprocess
import sys
import time

from base import Base
import wrapperutils as utils
import wrapperexceptions as exceptions


# meaning of the numerical values of runMain() return codes
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


class atlas(Base):
       
        def __init__(self, opts):
     
                super(atlas,self).__init__(opts) 
                self.source = utils.source()
                self.log.info('atlas: Object initialized.')

        # =========================================================== 
        #                      PRE-PROCESS 
        # =========================================================== 
           

        def pre_run(self):

                self.log.debug('pre_run: Starting.')

                rc = self._checkcvmfs()
                if rc != 0:  
                    return rc

                utils._testproxy()
                self._downloadtarball()
                if not self._checksum():
                        self.log.error('pre-run: pilot code checksum does not match the input option value. Aborting')
                        return 1
                self._untar()

                self.log.debug('pre_run: Leaving.')
                return 0  # FIXME: check every step

        def _checkcvmfs(self):
                '''
                quick & dirty test to check if CVMFS is functional
                '''
                self.log.debug('Starting.')

                cmd = 'timeout 10 time -p ls /cvmfs/atlas.cern.ch/repo/sw/'
                rc, out = commands.getstatusoutput(cmd)
                self.log.debug('rc and output of command %s: %s, %s' %(cmd, rc, out))
                self.log.debug('Leaving.')
                return rc
        
        def _downloadtarball(self):
                """
                downloads the pilot code tarball.

                The actual variable self.tarball is created in here 
                during the process
                The reason it is created here and not in base.py
                is because the URL is actually got from getScript() 
                which is very ATLAS specific. 
                So the whole process is not generic enough to be done in base.py 
                """
        
                self.log.debug('downloadtarball: Starting.')
    
                ### BEGIN TEST 0.9.13 ###
                #libcode = self.opts.pilotcode
                #script = self._getScript(libcode)
                #filename = script+'.tar.gz'
                filename = self._getScript(self.opts.pilotcode)
                ### END TEST 0.9.13 ###

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

        def _checksum(self):
                """                 
                if needed, verify the checksum of the pilot code tarball
                """                 

                if self.opts.pilotcodechecksum:
                    return self.tarball.verifychecksum(self.opts.pilotcodechecksum)
                else:
                    # not needed to verify it.
                    return True


        def _untar(self):
                self.tarball.untar()

        
        # =========================================================== 
        #                      RUN 
        # =========================================================== 

        def run(self):

            self.log.debug('run: Starting.')
            ### BEGIN TEST : SINGULARITY ###
            use_singularity = False  # FIXME: temporary solution
            if "SINGULARITY_INIT" not in os.environ.keys():
                container_type, container_options = self._check_for_singularity() 
                self.log.info('container_type = %s' %container_type)
                self.log.info('container_options = %s' %container_options)
                if container_type == 'singularity:wrapper':
                    use_singularity = True

            if use_singularity:
                    self.rc = self._run_singularity(container_options)
            else:
                pilotargs = self._pilotargs()
                if self.opts.shell:
                    self.rc = self._run_shell(pilotargs)
                else:
                    self.rc = self._run(pilotargs)

            return self.rc 
            ### END TEST : SINGULARITY ###


        ### BEGIN TEST : SINGULARITY ###
        def _run_singularity(self, container_options):
            """
            re-run the wrapper inside the container
            """
            self.log.debug('attempt to re-run the wrapper inside the container')

            os.environ['SINGULARITYENV_PATH'] = os.environ['PATH']
            os.environ['SINGULARITYENV_LD_LIBRARY_PATH'] = os.environ['LD_LIBRARY_PATH']

            wrapper_cmd = 'python '
            wrapper_cmd += '%s/wrapper.py ' %os.getcwd()
            wrapper_cmd += ' '.join(sys.argv[1:])
            cmd = 'singularity exec %s /cvmfs/atlas.cern.ch/repo/containers/images/singularity/x86_64-centos6.img %s' %(container_options, wrapper_cmd) 
            self.log.debug('command to re-run the wrapper inside the container is %s' %cmd)

            container_process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
            (out, err) = container_process.communicate()
            self.log.debug('dumping the output of running singularity command:')
            self.log.info(out)
            self.log.debug('output from singularity command ends here')
            self.log.debug('dumping the error of running singularity command:')
            self.log.info(err)
            self.log.debug('error from singularity command ends here')

            self.rc = container_process.returncode
            self.log.debug('rc from re-running the wrapper inside the container was %s' %self.rc)
            return self.rc

          

        def _check_for_singularity(self):
            """
            check if there fields in AGIS related container
            have any info
            """
            self.log.debug('checking for container-related fields in AGIS')
            cmd = 'curl --connect-timeout 20 --max-time 120 -sS "http://pandaserver.cern.ch:25085/cache/schedconfig/%s.all.json"' %self.opts.batchqueue
            self.log.debug('curl command is %s' %cmd)
            rc, out = commands.getstatusoutput(cmd)
            #FIXME
            # check if rc is 0 or not. For now, we assume curl worked fine
            doc = json.loads(out)
            container_type = doc['container_type']
            container_options = doc['container_options']
            # FIXME: temporary solution
            return container_type, container_options
        ### END TEST : SINGULARITY ###


        def _run(self, opt_l):
                """
                runs the pilot in the same process
                opt_l is a list of input parameters for method pilot.runMain()
                """
                self.log.debug('Starting.')
                self.log.debug('pilot args are = %s' %opt_l)
                # import and invoke the ATLAS pilot code
                import pilot
                self.rc = pilot.runMain(opt_l)
                msg = rc_msg.get(self.rc, "")
                if msg:
                    msg = "(%s)" %msg
                if self.rc != 0:                
                    self.log.warning('pilot returned rc=%s %s' %(self.rc, msg))
                else:
                    self.log.info('pilot returned rc=0')
                self.log.debug('Leaving with rc=%s.' %self.rc)
                return self.rc 


        def _run_shell(self, opt_l):
                """
                runs the pilot in a subshell 
                opt_l is a list of input parameters for method pilot.runMain()
                """

                self.log.debug('Starting.')
                self.log.debug('pilot args are = %s' %opt_l)

                cmd = 'python pilot.py '
                for opt in opt_l:
                    cmd += opt

                pilot_shell = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
                out = None
                (out, err) = pilot_shell.communicate()
                self.rc = pilot_shell.returncode

                msg = rc_msg.get(self.rc, "")
                if msg:
                    msg = "(%s)" %msg
                
                if self.rc != 0:                
                    self.log.warning('run: pilot returned rc=%s %s' %(self.rc, msg))
                else:
                    self.log.info('run: pilot returned rc=0')

                self.log.debug('run: Leaving with rc=%s.' %self.rc)
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
                                self.log.info('Adding $OSG_WN_TMP=%s as value of input option -d' %wndir)
                        elif 'TMP' in os.environ.keys():
                                wndir = os.environ['TMP']
                                self.log.info('Adding $TMP=%s as value for input option -d' %wndir)
                        else:
                                self.log.warning('no value found for input option -d')

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
                self.log.debug('post_run: Starting.')
                self._exit()
                self.log.debug('post_run: Leaving.')
                return 0  # FIXME!! check every step !! 

        def _exit(self):
                '''
                if we leave job.out there it will appear in the output 
                for the next pilot, even if it does not run any job 
                '''
                self.log.debug('exit: Starting.')
                os.system('rm -f job.out')
                os.system('rm -f *py') 
                os.system('rm -f *pyc') 
                os.system('rm -f stageoutlock') 
                self.log.debug('exit: existing with RC = %s.' %self.rc)
