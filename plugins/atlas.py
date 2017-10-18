#!/usr/bin/env python 

import commands
import getopt
import os
import sys
import time

from base import Base
import wrapperutils as utils
import wrapperexceptions as wexceptions
import validations
import pilotsource

try:
    import json as json
except ImportError, err:
    import simplejson as json



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
        ###self.source = utils.source()

        self.schedconfig = self._readschedconfig()
        if not self.schedconfig:
            # FIXME ?? is proper to abort is schedconfig is not reachable ??
            # FIXME ?? does anyone catch this exception ??
            raise Exception

        self.log.info('atlas: Object initialized.')

    # =========================================================== 
    #          PRE-PROCESS 
    # =========================================================== 
       

    def pre_run(self):

        self.log.debug('pre_run: Starting.')

        rc = validations._checkcvmfs()
        if rc != 0:  
            return rc

        utils._testproxy()

        rc = self._getpilotcode()        
        if rc != 0:
            self.log.critical('getting the pilot code failed.')
            return rc

        # FIXME: this should be in a better place. But for the time being...
        os.environ['ATLAS_SETUP_BASE_DIR'] = '/cvmfs/atlas.cern.ch/repo/sw/'  #DEFAULT
        os.environ['ATLAS_LOCAL_ROOT_BASE'] = '/cvmfs/atlas.cern.ch/repo/ATLASLocalRootBase'
        
        # FIXME: ?? should it be an exception instead of an RC ??
        rc = self._presetup()
        if rc != 0:
            self.log.critical('something went wrong with atlas setup. Aborting.')
            return rc
        
        # FIXME: ?? should it be an exception instead of an RC ??
        rc = self._setupatlas()
        if rc != 0:
            self.log.critical('something went wrong with atlas setup. Aborting.')
            return rc
        
        # FIXME: ?? should it be an exception instead of an RC ??
        rc = self._setupddm()
        if rc != 0:
            self.log.critical('something went wrong with atlas setup. Aborting.')
            return rc
        
        # FIXME: ?? should it be an exception instead of an RC ??
        rc = self._postsetup()
        if rc != 0:
            self.log.critical('something went wrong with atlas setup. Aborting.')
            return rc

        self.log.debug('pre_run: Leaving.')
        return 0  # FIXME: check every step



    def _getpilotcode(self):

        self.log.debug('Starting')

        pilotcode = pilotsource.PilotCodeManager(self.opts.pilotcode, 
                                                 self.opts.pilotcodechecksum, 
                                                 self.opts.pilotcoderatio) 
        rc = pilotcode.get()
        return rc


    def _presetup(self):
        '''
        method to source the content of AGIS field presetup 
        '''

        self.log.debug('_presetup: Starting')
        rc = self._setupfromschedconfig('autosetup_pre') 
        if rc != 0:
            self.log.critical('_presetup failed. Aborting.')
        self.log.debug('_presetup: Leaving')
        return rc  # FIXME: ?? should it be an Exception  when !=0 ??


    def _postsetup(self):
        '''
        method to source the content of AGIS field postsetup 
        '''

        self.log.debug('_postsetup: Starting')
        rc = self._setupfromschedconfig('autosetup_post') 
        if rc != 0:
            self.log.critical('_postsetup failed. Aborting.')
        self.log.debug('_postsetup: Leaving')
        return rc  # FIXME: ?? should it be an Exception  when !=0 ??
    


    def _setupatlas(self):
        '''
        source the global setup.sh global ATLAS setup file
        '''
    
        self.log.debug('_setupatlas: Starting.')
    
        basedir = os.environ['ATLAS_SETUP_BASE_DIR']
        setuppath = os.path.join(basedir, 'local/setup.sh')

        if not os.path.isfile(setuppath):
            self.log.info('setupatlas: setup file %s does not exist' %setuppath)
            raise wexceptions.WrapperExceptionSource(setuppath)
        else:
            cmd = 'source %s -s %s' %(setuppath, self.opts.wmsqueue)
            self.log.info('_setupatlas: sourcing command: %s' %cmd)
            ###rc, out = self.source(cmd)
            rc, out = utils.source(cmd)
            self.log.debug('_setupatlas: rc, output of sourcing cmd %s:\n%s\n%s' %(cmd, rc, out))
            utils._displayenv('local/setup.sh')
            utils._printsyspath('local/setup.sh')
    
        self.log.debug('_setupatlas: Leaving.')
        return rc


    def _setupddm(self):
        '''
        
        source the DDM ATLAS setup file
        '''
        
    
        self.log.debug('_setupddm: Starting.')
    
        # BEGIN TEST #
        # new way to source rucio
        #basedir = os.environ['ATLAS_SETUP_BASE_DIR']
        #setuppath = os.path.join(basedir, 'ddm/latest/setup.sh')
        basedir = os.environ['ATLAS_LOCAL_ROOT_BASE']
        setuppath = os.path.join(basedir, 'x86_64/rucio-clients/current/setup.sh')
        # END TEST #


        if not os.path.isfile(setuppath):
            self.log.info('setupddm: setup file %s does not exist' %setuppath)
            raise wexceptions.WrapperExceptionSource(setuppath)
        else:
            cmd = 'source %s -s %s' %(setuppath, self.opts.wmsqueue)
            self.log.info('_setupddm: sourcing command: %s' %cmd)
            ###rc, out = self.source(cmd)
            rc, out = utils.source(cmd)
            self.log.debug('_setupddm: rc, output of sourcing cmd %s:\n%s\n%s' %(cmd, rc, out))
            utils._displayenv('rucio setup')
            utils._printsyspath('rucio setup')
    
        self.log.debug('_setupddm: Leaving.')
        return rc

    def _readschedconfig(self):
            '''
            
            downloads schedconfig dictionary from URL
            '''
            
    
            self.log.debug('_readschedconfig: checking schedconfig for specific setup commands')
            cmd = 'curl --connect-timeout 20 --max-time 120 -sS "http://pandaserver.cern.ch:25085/cache/schedconfig/%s.all.json"' %self.opts.wmsqueue
            self.log.debug('_readschedconfig: curl command is %s' %cmd) 
    
            ntrials = 3
            for i in range(ntrials):
    
                self.log.info('_readschedconfig: trial %s for command %s' %(i+1, cmd))
                rc, out = commands.getstatusoutput(cmd)
                # out is json format. With json.load() we will convert it into a dictionary    
                if rc == 0:
                    self.log.debug('content of schedconfig is %s' %out)
                    schedconfig = json.loads(out)
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
                return None
    
            self.log.debug('_readschedconfig: Leaving')
            return schedconfig 



    def _setupfromschedconfig(self, field):
        '''
            
        method to source the content of nay AGIS field 
        if it exists
        For example, field can be "autosetuppre" or "autosetuppost"
        '''
            

        self.log.debug('_setupfromschedconfig: Starting for field %s' %field)

        if field not in self.schedconfig.keys():
            self.log.warning('%s not in schedconfig output' %field)
            # FIXME ?? should it be rc != 0 ??
            return 0
            
        setup = self.schedconfig[field]  
        self.log.info('_setupfromschedconfig: content of AGIS attribute is %s' %setup)

        if setup == None or setup == '':
            self.log.info('_setupfromschedconfig: nothing to do')
            return 0

        # if setup is not empty...

        if setup.startswith('http://') or setup.startswith('https://'):
            # content of AGIS field is not the path to the file,
            # it is an URL
            # we need to download it first
            # FIXME: try N times
            rc, out = commands.getstatusoutput('wget -qO %s.sh %s' %(field, setup))  #FIXME, find a better way than commands. something builtin in python
            if rc != 0:
                self.log.critical('_setupfromschedconfig: downloading %s failed' %setup) 
                return 1  #FIXME maybe raise an exception
            else:
                setup = './%s.sh' %field

        elif setup.startswith('file://'):
            setup = setup[7:]

        cmd = "source %s" %setup
        ###rc, out = self.source(cmd) 
        rc, out = utils.source(cmd) 
        self.log.debug('_setupfromschedconfig: rc, output of sourcing cmd %s:\n%s\n%s' %(cmd, rc, out))
        utils._displayenv('setup')
        utils._printsyspath('setup')
        self.log.debug('_setupfromschedconfig: Leaving')
        return rc


    
    # =========================================================== 
    #          RUN 
    # =========================================================== 

    def run(self):

        self.log.debug('run: Starting.')

        pilotargs = self._pilotargs()
        self.log.debug('run: pilot args are = %s' %pilotargs)

        # import and invoke the ATLAS pilot code
        import pilot
        self.rc = pilot.runMain(pilotargs)
        
        if self.rc != 0:        
            self.log.warning('run: pilot failed with rc=%s' %self.rc)
        else:
            self.log.info('run: pilot succeeded with rc=0')

        self.log.debug('run: Leaving with rc=%s.' %self.rc)
        return self.rc 

    def _pilotargs(self):
        """
        prepares the list of input arguments for pilot.py
        """

        self.log.debug('Starting.')

        extraopts = self.opts.extraopts

        # add -s and -h to extraopts
        if ' -s ' not in extraopts:
            self.log.info('Adding "-s %s" to pilotargs' %self.opts.wmsqueue)
            extraopts += ' -s %s' %self.opts.wmsqueue
        if ' -h ' not in extraopts:
            batchqueue = self.schedconfig['nickname']
            self.log.info('Adding "-h %s" to pilotargs' %batchqueue)
            extraopts += ' -h %s' %batchqueue



        # check if -d is in extraopts
        # if not, we use the value of $OSG_WN_TMP if defined (or $TMP otherwise)
        wndir = None 
        if ' -d ' not in extraopts:
            if 'OSG_WN_TMP' in os.environ.keys() and \
                               os.environ['OSG_WN_TMP'] != "" and \
                               os.environ['OSG_WN_TMP'].lower() != "none" and \
                               os.environ['OSG_WN_TMP'].lower() != "null":
                wndir = os.environ['OSG_WN_TMP']
                self.log.info('Adding $OSG_WN_TMP=%s as value of input option -d' %wndir)
            elif 'TMP' in os.environ.keys():
                wndir = os.environ['TMP']
                self.log.info('Adding $TMP=%s as value for input option -d' %wndir)
            else:
                self.log.warning('no value found for input option -d')

        if wndir:
            # This is needed for places like UCSD where $OSG_WN_TMP is $_CONDOR_SCRATCH_DIR
            if wndir[0] == '$' and wndir[1:] in os.environ.keys():
                self.log.info('content of wndir is itself an environment variable. Extracting value...')
                wndir = os.environ[ wndir[1:] ]
    

        if wndir:
            extraopts += " -d %s" %wndir

        # Finally we convert the string into a list
        pilotargs = extraopts.split()
        self.log.debug('Leaving with list %s.' %pilotargs)
        return pilotargs 

    


    # =========================================================== 
    #          POST-PROCESS 
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
