#!/usr/bin/env python 

import commands
import logging
import os
import time


log = logging.getLogger('wrapper.monitor')

def monping(action, rc=0):

    log.debug('Starting')
    
    # environment variables
    APFMON = os.environ.get('APFMON', None)
    APFFID = os.environ.get('APFFID', None)
    APFCID = os.environ.get('APFCID', None)

    if not APFMON or not APFFID or not APFCID:
        log.warning('undefined environment variables needed to call the web monitor')
        return

    if action == 'running':
        cmd = 'curl -ksS -d state=%s --connect-timeout 10 --max-time 20 %s/jobs/%s:%s' %(action, APFMON, APFFID, APFCID)
    elif action == 'exiting':
        cmd = 'curl -ksS -d state=%s -d rc=%s --connect-timeout 10 --max-time 20 %s/jobs/%s:%s' %(action, rc, APFMON, APFFID, APFCID)
    else:
        log.error('unrecognized action %s' %action) 
        return

    # run the command
    delay = 30
    ntrial = 0
    maxtrials = 1
    
    while True:
        log.debug('attemp monitor command %s trial %s' %(cmd, ntrial+1))
        rc, out = commands.getstatusoutput(cmd)
        log.debug('rc, out from monitor command %s: %s, %s' %(cmd, rc, out))
        if rc == 0:
            break
        else:
            log.error('monitor command %s failed')
            ntrial += 1
            if ntrial >= maxtrials:
                break
            time.sleep(delay)
            
    log.debug('Leaving')
