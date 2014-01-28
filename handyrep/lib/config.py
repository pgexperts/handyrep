from configobj import ConfigObj, Section
from error import CustomError
from validate import Validator
from datetime import datetime
import re
import os

class ReadConfig(object):

    def __init__(self, configfile):
        self.configfile = configfile

    def read(self, validationfile=None):
        try:
            if validationfile:
                ConfigObj(self.configfile,configspec=validationfile,stringify=True)
            else:
                config = ConfigObj(self.configfile)
        except:
            raise CustomError('CONFIG','Could not read configuration file %s' % self.configfile)

        if validationfile:
            validator = Validator()
            ctest = config.validate(validator)
            if not ctest:
                raise CustomError('CONFIG','Configuration file has bad format or out-of-range values')

        cdict = self.convertdict(config)
        return cdict

    def plainread(self):
        try:
            config = ConfigObj(self.configfile)
        except:
            raise CustomError('CONFIG','Could not read configuration file %s' % self.configfile)
        return config
    
    def validate(self, validationfile):
        try:
            config = ConfigObj(self.configfile, configspec=validationfile, stringify=True)
        except:
            raise CustomError('CONFIG','Could not read configuration file %s' % self.configfile)
        validator = Validator()
        result = config.validate(validator)
        return result

    def convertdict(self, config):
        # takes a configobj configuration object
        # and converts it to a dictionary
        newdict = {}
        for dkey, dval in config.iteritems():
            if type(dval) == dict:
                newdict[dkey] = self.convertdict(dval)
            elif re.search(r'Section', str(type(dval))):
                newdict[dkey] = self.convertdict(dval)
            else:
                newdict[dkey] = dval

        return newdict

    def readtypes(self, cdict):
        # method to read a config dict and
        # change the dates and datetimes into datetime types
        # change on, off into booleans
        newdict = {}
        datere = re.compile(r'\d{4}-\d{1,2}-\d{1,2}',flags=re.U),
        for dkey, dval in cdict.iteritems():
            if type(dval) == str:
                # test for booleans first
                if dval.lower() in ('true','t','on'):
                    newdict[dkey] = True
                elif dval.lower() in ('false','f','off'):
                    newdict[dkey] = False
                elif re.match(datere,dval):
                    try:
                        nval = datetime.strptime(dval,'%Y-%m-%d')
                        newdict[dkey] = nval
                    except:
                        try:
                            nval = datetime.strptime(dval,'%Y-%m-%d %H:%M:%S')
                            newdict[dkey] = nval
                        except:
                            newdict[dkey] = dval
                else:
                    newdict[dkey] = dval
            elif type(dval) == dict:
                newdict[dkey] = self.readtypes(dval)
            elif re.search(r'Section', str(type(dval))):
                newdict[dkey] = self.readtypes(dval)
            else:
                newdict[dkey] = dval

        return newdict

    
