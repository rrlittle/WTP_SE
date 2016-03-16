""" This file contains the functions
    responsible for mapping.

    Mapping in this context refers to expanding shorthand strings to their full
        length versions. 
    Also adding information that needs to be provided externally. Such as
        what scales are used in each instrument, what phases and respondents 
        have seen which instruments. Things of that nature. 

        This file relies heavily on a statically defined constructs file that 
        must be maintained. This constructs file contains all the mapping
        information. 
    """


from .waisman_utils import load_json, prettify_str
from os.path import join
import logging

class MapManager:
    """ This object deals with expanding abbreviated strings.
        initializing it requires a path to a statically defined file
        that tells us what the abbreviations are.

        self.maps is a dictionary of mappings, the keys are types of maps,
        and the values are dictionaries with the mapping themselves.
        I know that's a bit confusing. hang with me. such as.
        {
            "map_type":{
                "abbreviation": "expanded version",
                ...
            },
            "map_type2":{...}
        } 


        """
    def __init__(self, 
        constructsPath = ['staticallyDefined', 'constructs.json'], 
        log = logging):
        """ initializing mapping from the statically defined constructs file
            located at path.

            creates self.instr_params which holds all the instrument parameters
                defined in file at constructsPath

            if file is not found. fileNotFoundError thrown
            """
        self.instr_params, \
        self.json_raw = self.load_mappings(join(*constructsPath), 
            log = log)
        # instr_params is instruments from constructs with mappings applied
        # json_raw is whole json document
        # sets self.maps to the Maps of the statically defined constructs

    def load_mappings(self, path, log = logging):
        """  __Returns__ Dict with definitions for params based on file.
                This function loads a json doc with a specific syntax 
                and returns it for use as a mapping.

                also saves self.maps
            """
        instr_params_raw = load_json(path)
        self.maps = instr_params_raw['Maps']
        instr_params = self.apply_mapping(instr_params_raw['Instruments'],
            key='Instruments', log=log)

        return instr_params, instr_params

    def apply_mapping(self, obj, line = '', key = None, log = logging):
        """ __Returns__ an object of the same type as the arg.
            but with the full names of anything found in the self.maps dict.
            
            args:   obj -> some object. We'll determine what it is and 
                            what to do with it
                    line -> Don't pass anything to this. it's important for 
                            formatting output recursively. that's all
                    log -> where to print info. 
                    key -> defines where to look for mappings in self.maps
                            if None, it will attempt to find one in obj
                                if it can't no mapping will be applied
                            if key is found in self.mapping that map type will 
                            be searched for expansions of obj


            
            What this does is... 
            - if it's a string. 
                then find the full length version and return it
                if no fulllength version can be found. return the original.
            - if it's a list. 
                go through the list and call this on each element
            - if it's a dict.
                go through the dict. 
                on each value call this on each element
            """
        from numbers import Number
        log.debug('%s--recursed-- obj-> %s ' %(line, str(obj)[0:30]))
        
        if(isinstance(obj,Number)): # in the case of obj being a number, 
            log.debug('%sObject was a number. converted to string.' % line)
            obj = str(obj)          #convert it to a string.
        
        ###############
        ## Determine what type the object is
        ###############
        obj_type = type(obj) # grab type of object
        
        ##############
        if(obj_type is str): #if obj is a string. 
            if key in self.maps:
                log.debug('%skey -> %s'%(line, key))
                # get the full length version if one can be found
                # if one can't be found then the same thing will be returned
                obj = self.get_full_length(obj, line = line+'\t',
                                        map_key=key, 
                                        log = log)
            else: log.debug('%s key %s not found in self.maps, not expanding.'%(
                line, key))
            return obj 

        ###############
        elif(obj):  # else try to recurse through
            line = line + '\t' # increase the indent. for the next recursion
            log.debug('%strying iterate through obj which is %s'%(line, 
                obj_type))
            
            # iterate through obj.
            for index,k in enumerate(obj):
                log.debug('%stype: %s. item:%s. key:%s.' %(line, 
                    obj_type, k, key))

                #apply maps to each obj. 
                if(obj_type is list):
                    obj[index] = self.apply_mapping(obj[index], 
                        key = key,
                        line = line, 
                        log = log)
                elif(obj_type is dict):
                    obj[k] = self.apply_mapping(obj[k], 
                        line = line, 
                        key= k,
                        log = log)
                else:
                    raise UnkownObjectTypeError(\
                        "This object is of an unrecognized type! %s"%obj_type)
            #after iterating through the whole collection
        else:
            raise UnkownObjectTypeError(\
                "This object is of an unrecognized type! %s"%obj_type)
        # object should now be fully updated as well as we know how.
        return obj

    def get_full_length(self, 
        string, 
        map_key=None,
        line = '', 
        log = logging):
        """ This returns the full length version of string
            from self.maps 
            if it's not found it returns string passed in unchanged.

            if you supply an erroneous map_key (i.e. one not found in 
            self.maps) it will raise an error
            
            args: 
                string->   The string to look for a mapping i.e. 
                                a long winded version exists
                line ->     Do not provide anything here, this is important for 
                                recursive formatting of output
                map_key->  a key in self.maps to limit search, if not 
                                provided no attempt to find an expansion will 
                                be made. 
                log ->      where output goes
            return: str, expanded version of string or string itself if 
                    no expansion found
            """
        if map_key is None: raise MappingNotFoundError(
                            "No mapping Provided for the string %s"%string)
        if map_key in self.maps:
            if string in self.maps[map_key]:
                expanded = self.maps[map_key][string] 
                log.debug('%sExpanding %s -> %s'%(line, string, expanded))
                return expanded
            else:
                log.debug('%sNo Mapping found for %s'%(line, string))
                return string
        else: raise MappingNotFoundError('Incorrect mapping key provided.')

    def get_scales_and_fullname(self, 
        instr_abbr, 
        instr_list = None,
        instr_full='', line = '',
        log = logging):
        """ Searches through self.instr_params to find instruments that match
            instr_abbr.

            ARGS:
                instr_abbr : instrument abbreviation, as returned from 
                    dbManager.parse_tablename
                instr_list : used to limit search, not required to supply 
                        anything
                instr_full : used internally, DO NOT SUPPLY ANYTHING
                line : USED INTERNALLY, DO NOT SUPPLY ANYTHING

            RETURNS:
                
                ------

            """
        if instr_list is None: # if no list provided
            instr_list = self.instr_params  # use the whole list
        
        scales = None # will be used to hold scales parsed from maps
        matches = []

        for instr in instr_list: # iterate through all instruments provided
            instr_dict = instr_list[instr]
                # instr_dict is dict of parameters for instrument
            
            match, portion = self.instrument_matches(instr_abbr, 
                instr_dict['abbreviation']) 

            if match: # if this instrument appears to be a match
                log.debug('%s %s appears to be part of %s (%s matched)'%(line,
                            instr_abbr, instr, instr_dict['abbreviation']))

                # grab the scales at this level. can be overwritten by lowers
                if 'scales' in instr_dict:
                    log.debug('%s adding scales %s'%(line, instr_dict['scales']))
                    scales = instr_dict['scales']


                # if there are extensions. recurse
                if 'extensions' in instr_dict: # then recurse
                    log.debug('%s --Extensions found: recursing'%(line + '\t'))
                    instr_abbrev_suffix = instr_abbr[len(portion):]
                        # the remainder of the abbreviation

                    lower_matches = self.get_scales_and_fullname(
                        instr_abbrev_suffix, 
                        instr_list = instr_dict['extensions'], 
                        instr_full = instr_full + instr + ' ', 
                        line = line + '\t', 
                        log = log   )
                                       
                    if len(lower_matches) == 0: continue # go onto the next instrument
                                                        # of the list
                    for lm in lower_matches:
                        if 'scales' in lm:    # if we found matches below
                            log.debug('%s scales found in lowers'%line)
                            tmpScales = dict()
                            if scales: tmpScales = dict(scales)  
                            tmpScales.update(lm['scales'])     # add scales
                            lm['scales'] = tmpScales

                        log.debug('%s match found in lowers. appending'%line)
                        matches.append(lm) 
                else: # if there are no extensions then this is terminal.
                    if instr_dict['abbreviation'] == instr_abbr: # is it a match
                        # if this is terminal & a match. 
                        to_ret = {}
                        if scales: to_ret['scales'] = scales
                        to_ret['name'] =  instr_full + instr

                        log.debug('%s Found matching Instrument: %s'%(line, 
                            to_ret['name']))

                        matches.append(to_ret)
                    else: 
                        log.debug('%s inpsecting instrument (%s)'%(line, 
                            instr_full + instr) 
                            +  ', abbreviation %s does not match %s.'%(
                                instr_dict['abbreviation'], instr_abbr))

            else: 
                log.debug("%s %s doesn't appear to match. %s:%s"%(line,
                    instr, instr_abbr, instr_dict['abbreviation'])) 

        # done iterating through list
        log.debug('%s %s matches found for %s in the instrument list'%(line,
            len(matches), instr_abbr))
        log.debug('%s returning matches: %s'%(line, matches))     
        return matches

    def instrument_matches(self, whole_instr, abbrev_portion):
        """     This checks if the whole_instr seems to include abbrev_portion
                ARGS: 
                    whole_instr = the whole instrument abbreviation, 
                                as would be found in tablename
                    abbrev_portion = a portion from the mapping of the
                                    whole  
                RETURNS:  True or False. 
            """
        whole_instr_portion = whole_instr[0:abbrev_portion.__len__()]
        return whole_instr_portion == abbrev_portion, abbrev_portion

class BadConstructsFile(Exception):
    """ Used when constructs file doesn't work as expected due to user error"""
    pass
class MappingNotFoundError(Exception):
    """ if no mapping in self.maps can be found"""
    pass
class UnkownObjectTypeError(Exception):
    """ for use in apply mapping, if we don't know how to 
            look through the object passed in. """
    pass


class unitTest:
    """ to do some tests on this file. just add them here. 
            we'll probably only do these manually.

            to run open a pyterm from outside this package run
            from db2es import mapManager
            mapManager.UnitTest() # and that should do it.
        """
    def __init__(self):
        logging.basicConfig(level=logging.INFO)
        l = logging.getLogger('mapManagerUnitTest')
        l.setLevel(logging.INFO)
        mm = MapManager(log=l)
        l.info(mm.instr_params)
        
        l.info('\n\nTesting Get Info\n\n')

        l.info('------\n')
        tname = 'bc_r1'
        l.info('Getting info for abbrev: %s'%tname)
        i = mm.get_scales_and_fullname(tname, log=l)
        l.info(i)
        
        l.info('------\n')
        tname = 'ap'
        l.info('Getting info for abbrev: %s'%tname)
        i = mm.get_scales_and_fullname(tname, log=l)
        l.info(i)
        
        # l.setLevel(logging.DEBUG)

        l.info('------\n')
        tname = 'ai'
        l.info('Getting info for abbrev: %s'%tname)
        i = mm.get_scales_and_fullname(tname, log=l)
        l.info(i)

        test_list = {
            'TEST':{
                "abbreviation":'a',
                "scales":{
                    'a':'AAAA',
                    'b':'BBBB'
                },
                'extensions':{
                    'CHILD TEST':{
                        "abbreviation":'i',
                        'scales':{
                            'a':'CCCCC',
                            'c':'DDDDD'
                        }
                    }
                }
            }
        }
        l.info('------\n')
        tname = 'ai'
        l.info('Getting info for abbrev: %s'%tname)
        i = mm.get_scales_and_fullname(tname, log=l, instr_list = test_list)
        l.info(i)

        l.info('------\n')
        tname = 'z'
        l.info('Getting info for abbrev: %s'%tname)
        i = mm.get_scales_and_fullname(tname, log=l)
        l.info(i)
        
        l.info('------\n')
        tname = 'au'
        l.info('Getting info for abbrev: %s'%tname)
        i = mm.get_scales_and_fullname(tname, log=l)
        l.info(i)
        
        l.info('------\n')
        tname = 'disc_dr'
        l.info('Getting info for abbrev: %s'%tname)
        i = mm.get_scales_and_fullname(tname, log=l)
        l.info(i)
        
        l.info('------\n')
        tname = 'tb'
        l.info('Getting info for abbrev: %s'%tname)
        i = mm.get_scales_and_fullname(tname, log=l)
        l.info(i)

        l.info('\n\nTesting Apply Mapping\n\n')

        from .dbManager import dbManager
        dbm = dbManager()

        # l = logging.getLogger(name='debugger')
        # l.setLevel(logging.DEBUG)

        tname = 'calc_4_visit_age'
        table_info = dbm.parse_tablename(tname,log=l)
        l.info('Raw parsing of %s -> \n%s'%(tname, prettify_str(table_info)))
        l.info('Expanding with apply_mapping')
        table_info_expanded = mm.apply_mapping(table_info,log=l)
        l.info('RETURNED ->\n%s'%prettify_str(table_info_expanded))


        tname = 'calc_mr_ai_t'
        table_info = dbm.parse_tablename(tname,log=l)
        l.info('Raw parsing of %s -> \n%s'%(tname, prettify_str(table_info)))
        l.info('Expanding with apply_mapping')
        table_info_expanded = mm.apply_mapping(table_info,log=l)
        l.info('RETURNED ->\n%s'%prettify_str(table_info_expanded))
