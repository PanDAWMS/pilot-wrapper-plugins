#!/usr/bin/env python 

'''
this is the module wrapper.py
'''

wrapper_tarball_version = "1.0.1"

import commands
import getopt
import logging
import sys
import time
import xml.dom.minidom

import wrapperutils as utils
import monitor

print "this is module wrapper.py version %s" %wrapper_tarball_version

major, minor, release, st, num = sys.version_info

# ---------------------------------------------------------------------------
#               C L A S S E S
# ---------------------------------------------------------------------------

class Options(object):
        ''' 
        class to handle the input options.
        These options are:
                - wmsqueue          = the PanDA site
                - pilotcode         = URIs with the pilot code, either a tarball or directly code to be invoked
                                      Example:   [/cvmfs/atlas.cern.ch/../pilot.py, http://bnl.gov/../pilot.tar.gz, http://atlas.cern.ch/../pilot.tar.gz], http://atlas.cern.ch/../pilot-rc.tar.gz
                                      which means, treat the first 3 together as a group, with failover from one to another, and the last one is another group
                - pilotcodechecksum = the checksums to validate the pilot code tarball
                                      Example:   None, 123, 123, 456
                                      Each one corresponding to each source in the pilotcode variable
                - pilotcoderatio    = the frequency ratios between the different pilot code sources 
                                      Example: 99,1
                                      which means try to first group in pilot code 99% of times, and the second group 1% of times
                - extraopts         = everything else. Most probably option for the pilot.
                - pilotcode         = the final pilot code to be executed. 
                - tarballchecksum   = the checksum to validate the wrapper tarball (to be ignored)
        ''' 

        def __init__(self):

                self.wmsqueue = ""
                self.wrappertarballurl = ""
                self.pilotcode = ""
                self.pilotcodechecksum = ""
                self.pilotcoderatio = ""
                self.plugin = ""
                self.loglevel = ""
                self.tarballchecksum = ""
                self.extraopts = ""

        def parse(self, input=sys.argv[1:]):
                '''
                method to parse a list of input options.
                By default it processes the input provided
                to the module.
                '''

                try:
                        opts, args = getopt.getopt(input, "", 
                                            ["wrapperwmsqueue=", 
                                            "wrappertarballurl=",
                                            "wrapperplugin=",
                                            "wrapperpilotcode=",
                                            "wrapperpilotcodechecksum=",
                                            "wrapperpilotcoderatio=",
                                            "wrapperloglevel=",
                                            "wrappertarballchecksum=",
                                            "extraopts="])
                except getopt.GetoptError, err:
                        print str(err)

                for k,v in opts:
                        if k == "--wrapperwmsqueue":
                                self.wmsqueue = v
                        if k == "--wrappertarballurl":
                                self.wrappertarballurl = v
                        if k == "--wrapperplugin":
                                self.plugin = v
                        if k == "--wrapperpilotcode":
                                self.pilotcode = v
                        if k == "--wrapperpilotcodechecksum":
                                self.pilotcodechecksum = v
                        if k == "--wrapperpilotcoderatio":
                                self.pilotcoderatio = v
                        if k == "--wrapperloglevel":
                                self.loglevel = v
                        if k == "--extraopts":
                                self.extraopts += " " + v

        def setuplog(self):
                '''
                setup a logging object
                Basically, initializes logging facility and setup the format

                There are two log Handler objects:

                    -- one sending every message being logged to the stdout.
                       Which messages will be logged depends on the log level:
                            -- default is WARNING
                            -- possible input values are DEBUG or INFO

                    -- one sending every ERROR or CRITICAL message to the stderr

                Format of messages looks like:

                    2013-03-04 20:55:17,394 (UTC) - main.base: DEBUG: base: pre_run: Starting.        

                '''

                self.log = logging.getLogger('wrapper')

                if major == 2 and minor == 4:
                    FORMAT='%(asctime)s (UTC) [ %(levelname)s ] %(name)s %(filename)s:%(lineno)d : %(message)s'
                else:
                    FORMAT='%(asctime)s (UTC) [ %(levelname)s ] %(name)s %(filename)s:%(lineno)d %(funcName)s(): %(message)s'

                formatter = logging.Formatter(FORMAT)
                formatter.converter = time.gmtime  # to convert timestamps to UTC

                #  -----  stdout  ----- 
                stdout = logging.StreamHandler(sys.stdout)
                stdout.setFormatter(formatter)

                loglevel = logging.WARNING  #default
                if self.loglevel == 'debug':
                        loglevel = logging.DEBUG
                elif self.loglevel == 'info':
                        loglevel = logging.INFO
                
                stdout.setLevel(loglevel)
                self.log.setLevel(loglevel)

                self.log.addHandler(stdout)

                #  -----  stderr  ----- 
                stderr = logging.StreamHandler(sys.stderr)
                stderr.setFormatter(formatter)
                stderr.setLevel(logging.ERROR)
                self.log.addHandler(stderr)


        def display(self):
                '''
                print the value of input options
                '''
                print "wmsqueue = ", self.wmsqueue
                print "wrappertarballurl = ", self.wrappertarballurl
                print "plugin = ", self.plugin
                print "pilotcode = ", self.pilotcode
                print "pilotcodechecksum = ", self.pilotcodechecksum
                print "pilotcoderatio = ", self.pilotcoderatio
                print "extraopts = ", self.extraopts
                                        

class Execution(object):
        '''
        class to perform actual execution:
                1) find out the right plugin
                2) import it
                3) call method execute() 
        '''
        def __init__(self, opts):

                self.log = logging.getLogger("wrapper.execution")
                self.opts = opts
                self.plugin_obj = None
                self.log.debug("Execution: Object initialized.")

        def __getplugin(self):
                '''
                This method is in charge of importing dynamically 
                the right plugin, accordingly with the info provided
                (name of the plugin, passed as an attribute in object opts)
                The name of the module to be imported is the name of the
                plugin + 'plugin'

                All plugin modules are supposed to be in directory /plugins/
                We use the built-in function __import__ to import 
                the right module for the plugin we need. 

                All plugin modules are supposed to implement a class Execution
                inherited from class 'Base' in plugins/base.py
                '''

                self.log.debug('getplugin: Starting')

                plugin_module_name = self.opts.plugin
                self.log.debug('getplugin: plugin selected is %s' %plugin_module_name)
                plugin_module = __import__('plugins.%s' %plugin_module_name, 
                                            globals(), 
                                            locals(), 
                                            plugin_module_name) 
                self.log.debug('getplugin: plugin imported')

                plugin_class = self.opts.plugin 

                return getattr(plugin_module, plugin_class)
                self.log.debug('getplugin: Leaving')

        def execute(self):
                '''
                Execution:
                        1) the plugin is searched and imported
                        2) the method execute() in the plugin is invoked
                '''

                self.log.debug('execute: Starting')

                try:
                        self.plugin_cls = self.__getplugin()
                        self.plugin_obj = self.plugin_cls(self.opts)
                        rc = self.plugin_obj.execute()
                        return rc
                except Exception, ex:
                        self.log.critical('execute: execution failed.') 
                        self.log.critical(ex)

                self.log.debug('execute: Leaving')

# ---------------------------------------------------------------------------
#               M A I N 
# ---------------------------------------------------------------------------

def main():
    

        opts = Options()
        opts.parse()
        opts.setuplog()
        opts.display()
        
        # calling the monitor needs to be done after setting the Logger
        monitor.monping('running')
        
        execute = Execution(opts)
        try:
            rc = execute.execute()
            monitor.monping('exiting', rc)
            sys.exit(rc)
        except Exception, ex:
            print "Exception captured: %s" %ex
            monitor.monping('exiting', 1)
            sys.exit(1)
            

if __name__ == "__main__":
        main()



