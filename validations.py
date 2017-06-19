#!/usr/bin/env python 


import logging
log = logging.getLogger('wrapper.validations')

import subprocess
def _checkcvmfs():
    '''
    quick & dirty test to check if CVMFS is functional
    '''
    log.debug('Starting')
    try:
        cmd = 'time -p ls /cvmfs/atlas.cern.ch/repo/sw/'
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        (out, err) = p.communicate(timeout=10)
        rc = p.returncode
        log.info('rc and output of command %s: %s, %s' %(cmd, rc, out))
        log.info('cvmfs validated')
        return rc
    except subprocess.TimeoutExpired, ex:
        log.critical("command %s expired" %cmd)
        return 1

###def _checkcvmfs(self):
###        '''
###        quick & dirty test to check if CVMFS is functional
###        '''
###        log.debug('Starting.')
###
###        cmd = 'timeout 10 time -p ls /cvmfs/atlas.cern.ch/repo/sw/'
###        rc, out = commands.getstatusoutput(cmd)
###        log.debug('rc and output of command %s: %s, %s' %(cmd, rc, out))
###        log.debug('Leaving.')
###        return rc



import sys
def _checkpythonversion(major, minor=None, micro=None):
    """
    check the python version. 
    In python 2.6.5, for example, 
            major is 2
            minor is 6
            micro is 5
    """

    log.debug('Starting')
    sys_major, sys_minor, sys_micro, sys_releaselevel, sys_serial = sys.version_info

    if major < sys_major:
        log.critical("major version %s is lower than system major version %s" %(major, sys_major)) 
        return 1
    
    if minor:
        if minor < sys_minor:
            log.critical("minor version %s is lower than system minor version %s" %(minor, sys_minor)) 
            return 1
        
    if micro:
        if micro < sys_micro:
            log.critical("micro version %s is lower than system micro version %s" %(micro, sys_micro)) 
            return 1

    # everything went fine...
    log.info('python version validated')
    return 0


import rpm
# documentation on how to manage RPMs from python
#   http://docs.fedoraproject.org/en-US/Fedora_Draft_Documentation/0.1/html/RPM_Guide/ch-rpm-programming-python.html
#
# reference of attributes can be queried can be found here:
#   http://rpm.org/api/4.4.2.2/header-py_8c-source.html
def _rpm():
    """
    list all installed RPMs
    """

    log.debug('Starting')

    ts = rpm.TransactionSet()
    mi = ts.dbMatch()

    rpms = {}
    for header in mi:
        # mi is not scriptable
        # so we iterate over it to create an object
        # that accepts indexes
        key = header[rpm.RPMTAG_NAME]
        rpms[key] = header


    log.debug('leaving')
    return rpms


def _printrpm():

    log.debug('Starting')
    # print, sorted by package name
    pckgnames = rpms.keys()
    pckgnames.sort()
    log.info('List of installed RPMs: BEGIN')
    for pckgname in pckgnames: 
        header = rpms[pckgname]
        log.info('%s-%s-%s' %(header[rpm.RPMTAG_NAME],
                                   header[rpm.RPMTAG_VERSION],
                                   header[rpm.RPMTAG_RELEASE]) )
    log.info('List of installed RPMs: END')
    log.debug('leaving')
