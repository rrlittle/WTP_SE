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


from .waisman_utils import load_json
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
        path = ['staticallyDefined', 'constructs.json'], 
        log = logging):
        """ initializing mapping from the statically defined constructs file
            located at path.

            if file is not found. fileNotFoundError thrown
            """
        self.instr_params, \
        self.json_raw = self.load_mappings(join(*path), log = logging)
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
        log.info('%s--recursed-- obj-> %s ' %(line, str(obj)[0:30]))
        
        if(isinstance(obj,Number)): # in the case of obj being a number, 
            log.info('%sObject was a number. converted to string.' % line)
            obj = str(obj)          #convert it to a string.
        
        ###############
        ## Determine what type the object is
        ###############
        obj_type = type(obj) # grab type of object
        
        ##############
        if(obj_type is str): #if obj is a string. 
            if key in self.maps:
                log.info('%skey -> %s'%(line, key))
                # get the full length version if one can be found
                # if one can't be found then the same thing will be returned
                obj = self.get_full_length(obj, line = line+'\t',
                                        map_key=key, 
                                        log = log)
            else: log.info('%s key %s not found in self.maps, not expanding.'%(line, key))
            return obj 

        ###############
        elif(obj):  # else try to recurse through
            line = line + '\t' # increase the indent. for the next recursion
            log.info('%strying iterate through obj which is %s'%(line, obj_type))
            
            # iterate through obj.
            for index,k in enumerate(obj):
                log.info('%stype: %s. item:%s. key:%s.' %(line, obj_type, k, key))
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
        if map_key is None: MappingNotFoundError("No mapping for the string")
        if map_key in self.maps:
            if string in self.maps[map_key]:
                expanded = self.maps[map_key][string] 
                log.info('%sExpanding %s -> %s'%(line, string, expanded))
                return expanded
            else:
                log.info('%sNo Mapping found for %s'%(line, string))
            

class MappingNotFoundError(Exception):
    """ if no mapping in self.maps can be found"""
    pass
class UnkownObjectTypeError(Exception):
    """ for use in apply mapping, if we don't know how to 
            look through the object passed in. """
    pass


class unitTest:
    def __init__(self):
        l = logging.getLogger('__name__')
        l.setLevel(logging.INFO)
        mm = MapManager(log=l)
        print(mm.instr_params)