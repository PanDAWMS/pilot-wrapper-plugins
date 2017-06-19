#!/usr/bin/env python 

"""doc string here !!!
"""

import commands
import getopt
import hashlib
import logging
import os
import random
import shutil
import sys
import tempfile
import time

# ---------------------------------------------------------------------------
#                       C L A S S E S 
# ---------------------------------------------------------------------------


class SysPath(object):

    def __init__(self):

        self.pwd = sys.path[0]
        len_python_path = 0
        pythonpath = os.environ.get('PYTHONPATH', None)
        if pythonpath:
            # remove duplicated items in pythonpaths
            # sys.path does not include them
            pythonpathlist = []
            for i in pythonpath.split(':'):
                if i not in pythonpathlist:
                    pythonpathlist.append(i)

            len_python_path = len(pythonpathlist)

        self.system = sys.path[1+len_python_path:]

    def rebuild(self, pythonpath):
        '''
        pythonpath is a list with content of env var PYTHONPATH
        '''

        # auxiliar function to remove trailing slash / from paths
        def removeslash(path): 
            if path.endswith('/'):
                path = path[:-1]
            return path        

        newsyspath = []
        newsyspath.append( self.pwd )
        for i in pythonpath:
            if i != "":
                i = removeslash(i) 
                newsyspath.append(i)
        newsyspath += self.system

        sys.path = newsyspath


class Tarball(object):

        def __init__(self, baseurl, filename):

                self.log = logging.getLogger("main.tarball")

                self.baseurl = baseurl 
                self.filename = filename 

        def download(self):
                
                if self.baseurl.startswith('http'):
                        st,out = self.download_from_URL()
                if self.baseurl.startswith('file'):
                        st,out = self.download_from_disk()
                return st,out

        def download_from_URL(self):
        
                self.log.debug('Starting.')

                url = '%s/%s' %(self.baseurl, self.filename)
                cmd = 'curl --connect-timeout 20 --max-time 120 -s -S %s -o %s' %(url, self.filename)
                self.log.info('download: command to download pilotcode: %s' %cmd)

                import socket
                hostname = socket.gethostname()
                
                ipinfo = commands.getoutput('ifconfig | grep Bcast')

                ntrial = 3
                for i in range(ntrial):
                        self.log.info('download: trial %s' %(i+1))
                        st,out = commands.getstatusoutput(cmd)
                        if st == 0:
                                self.log.info('download: command to download pilotcode: %s success at trial %s at hostname %s with IP %s' %(cmd, i+1, hostname, ipinfo))
                                break
                        else:
                                self.log.error('download: command to download pilotcode: %s failed at trial %s at hostname %s with IP %s with RC=%s and message=%s' %(cmd, i+1, hostname, ipinfo, st, out))
                                time.sleep(10)
       
                return st, out 
                self.log.debug('Leaving.')

        def download_from_disk(self):
        
                self.log.debug('Starting.')

                try:
                        src = "%s/%s" %(self.baseurl, self.filename)
                        # remove "file://" from path
                        src = src[7:]
                        # copy file
                        dest = "./%s" %self.filename
                        shutil.copyfile(src, dest)
                        return (0, "")  # maybe temporary solution
                except:
                        return (1, "")  # maybe temporary solution  
                        
                self.log.debug('Leaving')

        def untar(self):
        
                self.log.debug('untar: Starting.')
       
                # FIXME: find a better way
                if not self.filename.endswith('.tar.gz'):
                    self.log.debug('filename is not a tar.gz file. Nothing to do.')
                    return
 
                cmd = 'tar zxvf %s' %self.filename
                commands.getoutput(cmd)
                cmd = 'chmod -f +x *.py *.sh'
                commands.getoutput(cmd)
        
                self.log.debug('untar: Leaving.')
        

        def verifychecksum(self, md5):
                """
                validates the md5 checksum for the tarball, if requested
                """

                self.log.debug('Starting validation of pilot tarball checksum')
                
                if md5 == hashlib.md5(open(self.filename).read()).hexdigest():
                    self.log.info('md5 checksum for the pilot tarball validated')
                    return True
                else:
                    self.log.warning('md5 checksum for the pilot tarball not validated')
                    return False


        def clean(self):
        
                self.log.debug('clean: Starting.')
                cmd = 'rm %s' % self.filename
                commands.getoutput(cmd)
                self.log.debug('clean: Leaving.')
        


# ---------------------------------------------------------------------------
#                       F U N C T I O N S 
# ---------------------------------------------------------------------------



#def source(setupcmd):
#        """
#        this is a function to do 'source /path/to/setup.sh'
#        It is not easy to source a setup file in python. 
#        commands.getoutput('source /path/to/setup.sh') does not work
#        because commands executes actions in a subshell.
#        Trick:
#                (1) I create 2 temporary files, 
#                    one to record the RC from the sourcing command, 
#                    and one to record the new environment
#                (2) In the same command I source the setup file and 
#                    record the RC and the entire environment if the temporary file.
#                (3) I capture the possible output
#                (4) I read the temporary files, 
#                    and insert every line in the environment
#                (5) I remove the temporary files
#                (6) sys.path need to be updated, since env var PYTHONPATH
#                    is not reloaded once the python interpreter has started
#        
#        NOTE: we first create a copy of the environment to keep record of it
#        
#        NOTE: some env vars (in self.excluded) are not meant to change so we keep them 
#        """
#
#        syspath = SysPath() 
#
#        # env vars that should not change
#        excluded  = ['_', 'SHLVL']
#
#        # record the current env 
#        oldenv = {}
#        for k,v in os.environ.iteritems():
#            oldenv[k] = v
#
#        # step 1
#        fd1, envtmpfilename = tempfile.mkstemp()
#        fd2, rctmpfilename = tempfile.mkstemp()
#
#        # step 2
#        # check is setupcmd already ends with ; to avoid adding a second one.
#        # a commands like  "blah ;; blah" will fail because of the double ;;
#        if setupcmd.endswith(';'):
#                setupcmd = setupcmd[:-1]
#        cmd = '%s; echo $? > %s; printenv | sort > %s' %(setupcmd, rctmpfilename, envtmpfilename)
#        cmdout = commands.getoutput(cmd)
#        # so here cmdout is the output of setupcmd, 
#        # while rctmpfilename contains the RC of sourcing setupcmd
#        # and envtmpfilename constains the new environment
#
#        # step 4
#        envtmpfile = open(envtmpfilename)
#        rctmpfile = open(rctmpfilename)
#
#        # rctmpfilename only has one line, so we read rctmpfilename.readlines()[0]
#        # and we remove the trailing \n with [:1]
#        # and finally we convert the rc into an integer
#        rc = int( rctmpfile.readlines()[0][:1] )
#        
#        #for line in f.read().split('\n'):
#        #        key = line.split('=')[0]
#        #        value = '='.join(line.split('=')[1:])
#        #        os.environ[key] = value 
#        out = envtmpfile.readlines()
#        for line in out:
#                line = line[:-1]
#                key = line.split('=')[0]
#                value = '='.join(line.split('=')[1:])
#                if key not in excluded:
#                    os.environ[key] = value 
#
#        # step 5
#        envtmpfile.close()
#        os.remove(envtmpfilename)
#        rctmpfile.close()
#        os.remove(rctmpfilename)
#
#        # step 6
#        pp_in_env = os.environ.get('PYTHONPATH', None)
#        if pp_in_env:
#            pp = pp_in_env.split(':')
#        else:
#            pp = []
#
#        syspath.rebuild(pp)
#        
#        # return the RC and the output of sourcing setupcmd
#        return rc, cmdout

class source(object):

    def __init__(self):
        self.syspath = SysPath()

    def __call__(self, setupcmd):
        # env vars that should not change
        excluded  = ['_', 'SHLVL']

        # record the current env 
        oldenv = {}
        for k,v in os.environ.iteritems():
            oldenv[k] = v 

        # step 1
        fd1, envtmpfilename = tempfile.mkstemp()
        fd2, rctmpfilename = tempfile.mkstemp()

        # step 2
        # check is setupcmd already ends with ; to avoid adding a second one.
        # a commands like  "blah ;; blah" will fail because of the double ;;
        if setupcmd.endswith(';'):
                setupcmd = setupcmd[:-1]
        cmd = '%s; echo $? > %s; printenv | sort > %s' %(setupcmd, rctmpfilename, envtmpfilename)
        cmdout = commands.getoutput(cmd)
        # so here cmdout is the outptu of setupcmd, 
        # while tmpfile contains the new environment

        # step 4
        envtmpfile = open(envtmpfilename)
        rctmpfile = open(rctmpfilename)

        # rctmpfilename only has one line, so we read rctmpfilename.readlines()[0]
        # and we remove the trailing \n with [:1]
        # and finally we convert the rc into an integer
        rc = int( rctmpfile.readlines()[0][:1] )

        out = envtmpfile.readlines()
        for line in out:
                line = line[:-1]
                key = line.split('=')[0]
                value = '='.join(line.split('=')[1:])
                if key not in excluded:
                    os.environ[key] = value

        # step 5
        envtmpfile.close()
        os.remove(envtmpfilename)
        rctmpfile.close()
        os.remove(rctmpfilename)

        # step 6
        pp_in_env = os.environ.get('PYTHONPATH', None)
        if pp_in_env:
            pp = pp_in_env.split(':')
        else:
            pp = []

        self.syspath.rebuild(pp)

        # return the RC and the output of sourcing setupcmd
        return rc, cmdout 







def getenv(var=None, mode=None):
        """
        function to get the content of the environment

        if var is None, then the whole environment is returned,
        otherwise, only that variable
        
        is mode is "break", then the value is broken-down in multiple lines. 
        """

        env = ''

        if var:
                vars = [var]
        else:
                vars = os.environ.keys()
                vars.sort()

        for var in vars: 
                value = os.environ.get(var)  
                if mode == 'break':
                        value = value.replace(':', '\n')
                env += '%s=%s\n' %(var, value)
        return env 

def setenv(var, value):
        '''
        function to setup an environment variable 
        '''
        os.environ[var] = value


def getScriptIndex(weights):
        """function returning a random number following a
        provided distribution of weights
        weights is a list a tuples (value, weight)

        Due the nature of the algorithm implemented
        the weights have to be sorted from the lower one to the higher one
        """
 
        n = random.uniform(0, 1)
        for (value, weight) in weights:
                if n < weight:
                        break
                n = n - weight
        return value


def _displayenv(id):

        log = logging.getLogger('main.utils')
        log.debug('%s: environment upgraded' %id)
        log.debug(getenv())
        log.debug('%s: version of python is %s' %(id, commands.getoutput('python -V')))
        log.debug('%s: path to python is %s' %(id, commands.getoutput('which python')))


def _printsyspath(id):
        """
        prints out the new content of sys.path
        """

        log = logging.getLogger('main.utils')
        log.debug('%s: sys.path upgraded' %id)
        log.debug(sys.path)


def _testproxy():

        log = logging.getLogger('main.utils')

        log.debug('_testproxy: Starting.')

        cmd = 'which voms-proxy-info 2> /dev/null'
        st, out = commands.getstatusoutput(cmd)
        if st==0:
                cmd = 'voms-proxy-info -all'
                log.debug("=== voms-proxy-info -all:")
                out = commands.getoutput(cmd)
                log.debug(out)

        log.debug('_testproxy: Leaving.')


def _check_curl_output(out):
        """
        check the output of a curl command is a valid string 
        and not an error message or random crap

        Note that in all these cases, the RC is always 0:

        Note, we are not going to consider as failed empty output

        $ curl  --connect-timeout 20 --max-time 60 "http://panda.cern.ch:25880/server/pandamon/query?tpmes=pilotpars&getpar=envsetup&queue=ANALY_BNL_SHORT-condor"
        source /afs/usatlas.bnl.gov/osg/pandasetup/@sys/current/envsetup.sh

        $ curl  --connect-timeout 20 --max-time 60 "http://panda.cern.ch:25880/server/pandamon/query?tpmes=pilotpars&getpar=envsetup&queue=ANALY_BNL_SHORT"
        No data found for siteid= queue=ANALY_BNL_SHORT

        $ curl  --connect-timeout 20 --max-time 60 "http://panda.cern.ch:25880/server/pandamon/query?tpmes=pilos&getpar=envsetup&queue=ANALY_BNL_SHORT-condor"
        Message received

        $ curl  --connect-timeout 20 --max-time 60 "http://panda.cern.ch:25880/server/panetpar=envsetup&queue=ANALY_BNL_SHORT-condor"
        <!DOCTYPE HTML PUBLIC "-//IETF//DTD HTML 2.0//EN">
        <html><head>
        <title>404 Not Found</title>
        </head><body>
        <h1>Not Found</h1>
        <p>The requested URL /server/panetpar=envsetup&amp;queue=ANALY_BNL_SHORT-condor was not found on this server.</p>
        <hr>
        <address>Apache Server at panda.cern.ch Port 25880</address>
        </body></html>
        """

        if out.startswith('No data found'):
            return False

        if out.startswith('Message received'):
            return False

        if out.startswith('<!DOCTYPE'):
            return False
    
        # if everything went OK
        return True


