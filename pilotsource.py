import commands
import logging
import os
import random
import sys

class PilotCodeManager(object):
    """
    class to manage all potential variables involved in getting the pilot code.j
    It will verifies that the number of options matches, when used,
    the number of checksum values.
    It will verifies that the number of options matches, the number of ratio values.
    Generates a random number, and creates the corresponding PilotCodeCollection object.
    If final return code is != 0, it raises and exception.

    Example:

            --wrapperpilotcode = ['file:///cvmfs/atlas.cern.ch/pilot.py', 'http://atlas.cern.ch/pilot.tar.gz'], 'http://atlas.cern.ch/pilot-devel.tar.gz'
            --wrapperpilotcodechecksum = 123,456,789
            --wrapperpilotcoderatio = 99,1

    will try 99% of the times to get the pilot code 
    from 'file:///cvmfs/atlas.cern.ch/pilot.py', with a failover to 'http://atlas.cern.ch/pilot.tar.gz'
    and 1% of the times from 'http://atlas.cern.ch/pilot-devel.tar.gz'
    """

    def __init__(self, sources, checksums=None, ratios=None):
        """
        sources, checksums (when used), and ratios (when needed)
        are strings splitted by comma
        """

        self.log = logging.getLogger("wrapper.pilotcodehandler")

        # just to avoid problems...
        if checksums and checksums.lower() == 'none':
            checksums = None
        if ratios and ratios.lower() == 'none':
            ratios = None
            

        # first step is to validate all input options
        rc = self._validateinputs(sources, checksums, ratios)
        if rc != 0:
            self.log.error('validating input options failed. Aborting')
            raise Exception
            # FIXME: maybe we need a custom Exception class 

        self.sources = self._parsesources(sources)

        self.checksums = self._remapchecksums(self.sources, checksums)

        if ratios:
            self.ratios = [int(ratio) for ratio in ratios.split(',')]
        else:
            self.ratios = None


        self.collections = self.createCollections()
        index = self.pickCollectionIndex(self.ratios)
        self.collection = self.collections[index]


    # FIXME
    def get(self):
        rc = self.collection.get()       
        return rc
 
        


    def createCollections(self):
        """
        creates a list of PilotCodeCollection objects
        with info from self.sources, and self.checksums
        """

        collections = []


        for i in range(len(self.sources)):

            sources = self.sources[i]
            checksums = self.checksums[i]
            
            collection = PilotCodeCollection(sources, checksums)
            collections.append(collection)

        return collections



    def pickCollectionIndex(self, ratios):
            """
            function returning the index for an item in self.collections
            given the distribution of ratios
            """

            if not ratios:
                # when there are no ratios is because there is only
                # one source, and only one collection
                # so we return 0, which would be the first index
                return 0
        

            # trick. 
            # We first create a list of tuples (ratio, index)
            # and we sort the list by ratio

            l = []
            for i in range(len(ratios)):
                if i == 0:
                    l.append( (ratios[i], i) )
                else:
                    l.append( (ratios[i] + l[i-1][1], i) )

            l.sort()
   
            n = random.uniform(0, 100)
            for (weight, index) in l:
                    if n < weight:
                            break
                    n = n - weight
            return index 




    def _parsesources(self, sources):
        """
        parses the string sources and returns a list of strings
        For example:
            "[/cvmfs/atlas.cern.ch/sw/pilot.py,http://atlas.cern.ch/sw/pilot.tar.gz],http://atlas.cern.ch/sw/pilot-rc.tar.gz"  
        must be splitted into 
            [ ["/cvmfs/atlas.cern.ch/sw/pilot.py","http://atlas.cern.ch/sw/pilot.tar.gz"], ["http://atlas.cern.ch/sw/pilot-rc.tar.gz"] ]    

        """
        out = []
      
        sources = sources.strip() 
        while len(sources) > 0:
      
            if sources[0] == ',':
                sources = sources[1:]
      
            elif sources[0] == '[':
                fclose = sources.find(']')
                subs = sources[1:fclose]
                tmp = []
                for s in subs.split(','):
                    tmp.append( s.strip() )
                out.append( tmp )            
                sources = sources[fclose+1:]
      
            else:
                fcomma = sources.find(',') 
                if fcomma == -1:
                    out.append([sources])
                    sources = ""
                else:
                    subs = sources[:fcomma].strip()
                    out.append( [subs] ) 
                    sources = sources[fcomma+1:]
      
            sources = sources.strip()
                
        return out
      

    def _remapchecksums(self, sources, checksums):
        """
        it converts the list of checksums (or a single None)
        into a list of lists following the same layout
        of sources
        For example, if sources is [ ['a', 'b'], ['c'] ]
        it converts "chk1, chk2, chk3" into [ ['chk1', 'chk2'], ['chk3'] ]
        and None into [ [None, None], [None] ]
        """
   
        out = []
    
        if checksums:
            tmp = checksums.split(',')
            # first we convert string "None" into object None
            for i in range(len(tmp)):
                tmp[i] = tmp[i].strip()
                if tmp[i].lower() == "none" or tmp[i].lower() == "null":
                    tmp[i] = None
        else:
            # tmp is [None, None, None, ..., None] 
            # as many as needed to equal the total number of sources
            tmp = [None] * sum( [len(i) for i in sources] )
            
        for i in sources:
            n = len(i)
            out.append( tmp[:n] )
            tmp = tmp[n:]
    
        return out



    def _validateinputs(self, sources, checksums, ratios):
        """
        to validate all number of values matches, we need to take into account:
            -- the length of self.sources is not necessarily the number of sources
               as each item in the list could also be a list of sources, to fail over
               So we need to get the entire list of sources
            -- However, the number of ratio values must much the length of self.sources
               unless no value is provided, assuming there is only one item in self.sources
            -- However, the number of checksum values must much the number of sources,
               unless it is 0 (no checksum value is provided)
        """
        # FIXME
        # Question: do we want to abort if there are more than one source but no ratios?
        #           currently, when no ratios, we use always index 0 to pick a given source

        # some preliminary baking of the input options (temporarily)
        sources = self._parsesources(sources)

        all_sources = []
        for i in sources:
            if type(i) is list:
                all_sources += i
            else:
                all_sources.append(i)

        if len(all_sources) == 0:
            self.log.error("list of source entries is empty")
            return 1
            
        if ratios:
            # some preliminary baking of the input options (temporarily)
            ratios = [int(ratio) for ratio in ratios.split(',')]
            if len(sources) != len(ratios):
                self.log.error("number of ratio values does not match the number of source entries")
                return 1
            if sum(ratios) != 100:
                self.log.error("the sum of ratios does not add up 100")
                return 1
                    

        if checksums:
            # some preliminary baking of the input options (temporarily)
            checksums = checksums.split(',')
            if len(all_sources) != len(checksums):
                self.log.error("number of checksum values does not match the number of source entries")
                return 1
            
        # if everything went OK...
        return 0
         
        
            
        


class PilotCodeCollection(object):
    """
    it contains all PilotCodeSource objects corresponding to the same ratio value.
    If more than one, it will failover from one to another.
    It will return the final return code (RC)
    """

    def __init__(self, sources, checksums):

        self.log = logging.getLogger("wrapper.pilotcodecollection")

        self.sources = sources
        self.checksums = checksums

        self.collection = []
        for i in range(len( self.sources )):
            source = sources[i]
            checksum = checksums[i]
            pilotcodesource = PilotCodeSource(source, checksum)
            self.collection.append( pilotcodesource )

        self.log.debug('object PilotCodeCollection created')


    def get(self):
        """
        tries, one by one, each object in the collection
        """

        for pilotcodesource in self.collection:
            rc = pilotcodesource.get()
            if rc == 0:
                return rc
        else:
            self.log.error('all attempt to get the pilot code source failed')
            return 1



class PilotCodeSource(object):
    """
    class that handle each individual source to get the pilot code from. 
    It downloads it when it is an URL (http or https).
    It copies -or do nothing- when it is from the filesystem.
    When used, verifies the checksum.
    If needed, untar the tarball.
    """

    def __init__(self, source, checksum):

        self.log = logging.getLogger("wrapper.pilotcodesource")

        self.source = source
        self.checksum = checksum
        self.filename = self.source.split('/')[-1]

    def get(self):

        rc = self._getpilotcode()
        if rc == 0:
            self._addsyspath()
        else:
            self.log.critical("getting the pilot code failed")
            return rc
        
        # if rc == 0...
        rc = self._validatechecksum()
        if rc != 0:
            self.log.critical("validation of pilot code checksum failed")
            return rc

        # if rc == 0...
        rc = self._untar()
        if rc != 0:
            self.log.critical("un tarring the pilot code tarball failed")
            return rc
       
        # if everything went OK..
        return 0


    def _getpilotcode(self):

        if self.source.startswith('http'):
            rc = self._getfromURL()
        elif self.source.startswith('file'):
            rc = self._getfromFS()
        else:
            self.log.critical('pilot source code does not start by "http" nor "file". Aborting')
            return -1
            
        return rc 


    def _getfromURL(self):

        self.log.debug('Starting.')
        
        cmd = 'curl --connect-timeout 20 --max-time 120 -s -S %s -o %s' %(self.source, self.filename)
        self.log.info('download: command to download pilotcode: %s' %cmd)
        
        import socket
        hostname = socket.gethostname()
        
        ipinfo = commands.getoutput('ifconfig | grep Bcast')
        
        ntrial = 3
        for i in range(ntrial):
            self.log.info('_getfromURL: trial %s' %(i+1))
            rc,out = commands.getstatusoutput(cmd)
            self.log.info('_getfromURL: rc, output of command %s : %s, %s' %(cmd, rc, out))
            if rc == 0:
                self.log.info('_getfromURL: command to download pilotcode: %s success at trial %s at hostname %s with IP %s' %(cmd, i+1, hostname, ipinfo))
                break
            else:
                self.log.error('_getfromURL: command to download pilotcode: %s failed at trial %s at hostname %s with IP %s with RC=%s and message=%s' %(cmd, i+1, hostname, ipinfo, rc, out))
                time.sleep(10)
        
        self.log.debug('Leaving.')
        return rc 


    def _getfromFS(self):

        self.log.debug('Starting.')
             
        if not self.filename.endswith('.tar.gz'):
            self.log.debug('filename %s is not a tarball. Not need to copy' %self.filename)
            return 0
        else:
            try:
                # remove "file://" from path
                src = self.source[7:]
                # copy file
                dest = "./%s" %self.filename
                shutil.copyfile(src, dest)
                return 0
            except:
                self.log.critical('copying the pilot code %s failed' %self.source)
                return 1
                

    
    def _addsyspath(self):
        '''
        add self.source to the sys.path
        
        if self.source is an URL, 
                then just add CWD
        if self.source is a tarball in the filesystem, 
                just add CWD
        if self.source is a file (no tarball) in the filesystem, 
                add the dirname
        '''
    
        self.log.debug('adding path to pilot code to sys.path')

        if self.source.startswith('http'):
            self.log.debug('pilot code is got from an URL, adding CWD to sys.path')
            sys.path.append(os.getcwd())
        elif self.source.startswith('file'):
            if self.source.endswith('.tar.gz'):
                self.log.debug('pilot code is tar file being copied to CWD, adding CWD to sys.path')
                sys.path.append(os.getcwd())
            else:
                self.log.debug('pilot code is got from a file, adding dirname() to sys.path')
                path = self.source[7:]
                path = os.path.dirname(path)
                sys.path.append(path)

        self.log.debug('path to pilot code added to sys.path')



    def _validatechecksum(self):
        """
        validates the md5 checksum for the tarball, if requested
        """
        
        self.log.debug('Starting validation of pilot tarball checksum')

        if not self.checksum:        
            self.log.debug('no checksum, nothing to do')
            return 0
        else:
            
            if not self.filename.endswith('.tar.gz'): 
                # we want to validate the actual original file. 
                # For example /cvmfs/atlas.cern.ch/repo/sw/PandaPilot/pilot/latest/pilot.py
                file = self.source
            else:
                # we validate the tarball after being downloaded 
                # or copied to PWD
                file = self.filename
            
            if self.checksum == hashlib.md5(open(file).read()).hexdigest():
                self.log.info('md5 checksum for the pilot tarball validated')
                return 0 
            else:
                self.log.warning('md5 checksum for the pilot tarball not validated')
                return 1


    def _untar(self):

        self.log.debug('_untar: Starting.')
        
        # FIXME: find a better way
        if not self.filename.endswith('.tar.gz'):
            self.log.debug('filename is not a tar.gz file. Nothing to do.')
            return 0
        
        cmd = 'tar zxvf %s' %self.filename
        rc,out = commands.getstatusoutput(cmd)
        self.log.info('rc and output of cmd %s :%s, %s' %(cmd, rc, out))
        
        self.log.debug('_untar: Leaving.')
        return rc

