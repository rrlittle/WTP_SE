'''
        ---------------------------------------------------------------
        ===     Usage: in bash shell. run 'python es_setup.py'      ===

        This script will go through the whole wtp_data and extract tables.
        It will parse each tablename and extract everything possible from them. 

        It also uses a statically defined mapping found in ./staticallyDefined/constructs.json

        It then populates an Elasticsearch database.    (It does naivley assume that there is an ES instance Running)
                                                        (if there's not it'll fail.                                 )
        with the populated struct.

        Be sure it's in the same directory as waisman_utils.py as it uses that package. 
        it's also dependent on the elasticasearch egg to be installed (use pip)

        log of updates
        ---------------
        5/19/2015 - initially wrote this readme. it works at this point.   
'''


import waisman_utils as u
from elasticsearch import Elasticsearch as es
import json

## BEGIN JSON AND MAPPING
####################
class MapManager:
    def __init__(self, path='staticallyDefined/constructs.json', debug=True):
        # when initialized. load the file in path
        # load the mappings from the file
        self.instr_params, self.json_raw = self.load_mappings(path, debug=debug)
            # instr params is the Instruments from constructs with mappings applied.
            # json_raw is the whole json document.
            # it also initialized self.maps which is the maps from constructs.

        #wait for data to apply mappings to.
        pass

    def log_mappings(self,path): # save the mappings to a file 
        import time
        f = open(path + time.strftime("-%a_%b_%Y-%H") + '.md','w')
        f.write('Raw Parameters File :\n')
        f.write(u.prettify_str(self.json_raw))
        f.write('\n\n---------------------------------\n')
        f.write('Mappings Struct:\n')
        f.write(u.prettify_str(self.maps))
        f.write('\n\n---------------------------------\n')
        f.write('Instrument Parameters:\n')
        f.write(u.prettify_str(self.instr_params))
        f.close()

    def get_json(self, path='constructs.json'): # returns a dict from a json file
        f = open(path,'r')
        return json.load(f)
    
    def load_mappings(self, path, debug=True): # returns instrument parameters with maps applied, raw json
        """ __Returns__ Dict with definitions for params based on file.
            This function loads a json doc with a specific syntax 
            and returns it for use as a mapping. 
            """
        instr_params_raw = self.get_json(path) # throws an error
        self.maps = instr_params_raw['Maps']
        instr_params = self.apply_mapping(instr_params_raw['Instruments'], debug=debug)

        return instr_params,instr_params_raw
    
    def apply_mapping(self, obj, line = '', debug = True): # returns an object with maps applied
        """ __Returns__ an object of the same type as the arg.
            but with the full names of anything found in the self.maps dict.
            args:   to = the obbject to apply the map to
                    attribName = the attributeToAttribute
    
            Throws a key error, if attribName doesn't exist in self.maps
            note assumes self.maps is;
                maps:{
                    'attributeToAttribute':{
                        'abrv':'fullLength'
                    }
                }
            
                What this does is... 
                - if it's a string. 
                    then find the full length version and return it
                    if no fulllength version can be found. return the original.
                - if it's a list. 
                    go through the list and call itself
                - if it's a dict.
                    go through the dict. 
                    on each key  call this
            """
        from numbers import Number
        if(debug):print('%s--recursed-- obj-> %s ' %(line, str(obj)[0:30]))
        
        if(isinstance(obj,Number)): # in the case of obj being a number, 
            if(debug):print('%sObject was a number. converted to string.' % line)
            obj = str(obj)          #convert it to a string.
        
        obj_type = type(obj)
        if(obj_type is str): #if obj is a string. 
            abrv = obj              # It is an abbreviation
            fulllength_abrv = self.get_full_length(abrv, line = line+'\t', \
                                    debug = debug) # get the full length version
            if(debug): 
                if(fulllength_abrv is not abrv):  # if it changed
                    print('%sApplying map to %s. -> %s' %(line, abrv,fulllength_abrv))
                else:       # if theyre the same
                    print('%sNo map found for %s.' %(line, abrv)) 
            return fulllength_abrv
        elif(obj): # if the object exists the obj should be iterable. recurse through it. 
            #if(debug): print('%siterating through: %s' %(line, obj_type))
            line = line + '\t' # increase the indent.
            
            # iterate through obj.
            for index,key in enumerate(obj):
                if(debug):print('%stype: %s. item:%s' %(line, obj_type, key))
                #apply maps to each obj. 
                if(obj_type is list):
                    obj[index] = self.apply_mapping(obj[index], line = line, debug = debug)
                if(obj_type is dict):
                    obj[key] = self.apply_mapping(obj[key], line = line, debug = debug)
            #after iterating through the whole collection
        else:
            print('%sThis is odd. if(obj) => False.. what\'s obj? obj= %s' % (line,obj))
        
        return obj
    
    def get_full_length(self, string, line = '', map_type=None, debug = True): # returns a string with map applied
        """This returns the full lenth verison of string. from self.maps
            if it's not found. it returns string. if you supply an erroneus 
                key such as map_type, or a string thats not in maps. it will 
                print an error message
            """
        if(map_type is not None):
            if(map_type in self.maps):                  # if they provide the map_type
                #print('%sChecking the type of string. in get_full_length type=%s' %(line,string))
                if(string in self.maps[map_type]):      # and the string is there as promised
                    return self.maps[map_type][string]  # return the full length string from maps
                else:
                    if debug: print('%sthe argument string, %s,  is not in self.maps[%s]' % (line,string, map_type))
            else:
                if debug: print('the argument map_type, %s, is not in self.maps' % map_type)
            return string # if either test failed. return string unadulterated
        # if map_type not provided search through the maps until you find a key matching string.
        for map_type in self.maps:
            fulllength = self.get_full_length(string, map_type = map_type, line = line, debug = debug)
            if (string is not fulllength): # then we found a match!
                return fulllength
            #else contnue searching
        #if we get here. we have searched through the whole of maps and found nothing. 
        return string

    def get_info(self, instr_abbrev, instr_full=None, instr_list = None, line ='', debug = True): # gets scales and name
        """ Search for instrument with abbreviation that matches.
            if there are any scales, return them. they will be in the form of a dict
            If instrument name can be determined return that as well

            if No scales found return None
                ARGS:
                instr_abbrev -> the abbreviation of the instrument we're lookng for
                instr_list -> the list of instrument maps _defaults_ to self.instr_params

                RETURNS:
                    the dict of scales if found. None if not found.
                    the name of the instrument as can best be determined  

                recall that constructs should support nested instruments.  by way of extension.
                recall constucts is in the forms
                {
                    'instr name':{
                        'abbreviation':''
                        'extensions':{
                            'instrument name':{ 
                                'abbreviation':''
                                'scales':{}
                                'memo':''
                                'details':''
                            }
                        }
                        'scales'
                    }
                }

            """
        
        if(not instr_list): # if no list provided use the whole parameters list.
            instr_list = self.instr_params 

        scales = None # scales will hold the scales from maps.
        for instr in instr_list: # iterate through all instruments provided.
            instr_dict = instr_list[instr] # instr_dict is the parameters dict for inst
            #_check_ if this is the correct instrument. 
            if(instr_abbrev.startswith(instr_dict['abbreviation'])): # 
                if(debug): print('%sFound beginning of %s in:' %(line, instr_abbrev))
                if(debug): print('%s\"%s\" %s' %(line, instr, u.prettify_str(instr_dict).replace('\n','\n\t'+line)))
                
                if(not instr_full): instr_full = ''
                instr_full = instr_full + instr +' ' # track full instrument name. Lower levels should append their additions
                if(debug): print('%sinstrument name = %s...' %(line,instr_full))
                
                # if there are extensions. recurse
                if('extensions' in instr_dict): # then recurse. 
                    if(debug): print('%s---Extensions found: Recursing' %(line+'\t'))
                    instr_abbrev_suffix = instr_abbrev[instr_dict['abbreviation'].__len__():] # save after map abrv
                    # recurse down
                    lower_scales, instr_full = self.get_info( instr_abbrev_suffix, instr_full=instr_full, instr_list = instr_dict['extensions'], line = (line + '\t'), debug=debug) 
                    if(lower_scales):       # if it found something
                        if(not scales): scales = {}          # if scales doesn't exist initialize it
                        scales.update(lower_scales)          # add it to scales.  
                # if there are no extensions and instr_abrv doesn't match. Then return None.
                elif(instr_dict['abbreviation'] != instr_abbrev):  
                    if(debug): print('%sNothing Found. The abbreviations don\'t match. .%s:%s.' \
                                            % (line+'\t', instr_abbrev, instr_dict['abbreviation']))
                    return None, instr_full

                if('scales' in instr_dict): # then add them to the dict for return
                    if(debug): print('%sScales found!' % line)
                    if(not scales): scales ={}                      # if scales doesn't exist initialize it
                    scales.update(instr_dict['scales'])             # add scales from instr_list to scales
                if(debug): print('%sReturning scales as %s' %(line, str(scales)[:30]))
                return scales, instr_full
        return None, instr_full       # if you iterate through all instruments. and none returns. then failed.   



    ###################
    ## End JSON and Mapping

##BEGIN DATABASE MANAGEMENT
################
class dbManager:
    def open_db(self):
        self.cur = u.open_db_con()
        return self.cur.tables()
    
    def close_db(self):
        u.close_db_con()
        pass
    
    def open_es(self):
        self.e = es()
        return self.e
        
    def close_es(self):
        pass # it looks like nothing bad happens if you leave the connection hanging. 

    def insert_struct_to_es(self, struct, index, debug = True):
        """ puts a struct into the es. specify an index and the keys 
            specify the type. the actual subdicts form the es documents
            stuct of tables.
            """  
        for doc_type in struct: # table names are _type key in es
            x = self.e.index(index=index, doc_type=doc_type, body=struct[doc_type])
            if(debug): print(x)
        
    ################
    ## END DATABASE MANAGEMENT

    ## PARSING 
    ################
   

    def parse_row(self, row, debug = True): # get a dict with the attribute for this tablename
        """ Takes in a row from database cursor. returns dict with all attributes from tablename
            args:
                row : ['wtp_data', '', tablename, 'table', '']
                    This is the definition from the pypyodbc package. each row of 
                    cursosr.tables() is like that.  
            returns:
                {
                    'type': 'data'/'calc'/'misc'
                    'tablename': tablename,
                    'instrument abbreviation': ABES
                    'respondent': t/m/f
                    'phase' : 4
                    etc....
                }

            This function uses the mappings defined in the class variable table_name map. 
            which basically 
            """
        tablename_maps =\
            {
            'parsing maps':{
                 'data':{
                     'tablename':'table_split[0:]',
                     'phase':'table_split[1: 2]',
                     'instrument abbreviation':'table_split[2 : table_split.__len__()-1]',
                     'respondent':'table_split[-1]',
                 },
                 'calc':{
                     'tablename':'table_split[0:]',
                     'phase':'table_split[1: 2]',
                     'instrument abbreviation':'table_split[2: table_split.__len__()-1]',
                     'respondent':'table_split[-1]',
                     },
                 'misc':{
                     'tablename':'table_split[0:]',
                     }
            },
            'filters':{
                'data':{
                    'length':4,
                    'disallowed words':[
                        'dates'
                    ]
                },
                'calc':{
                   'length':4,
                    'disallowed words':[
                        'dates'
                    ]
                }
            },
            '__doc__': \
                """ This is the readme for this dict. This dict defines the parameters for 
                the WTP naming conventions. 
                        This has 3 sections. 
                            - This readme
                            - Parsing maps
                            - Filters

                        ___This readme___ is self explanatory.

                        ___Parsing maps___ has a bunch of commands to parse a tablename into various attributes.
                            the structure is like so:
                                type{
                                    'attribute this type should have 1'
                                    'attribute this type should have 2'
                                    etc. 
                                }
                            It is assumed that the tablename has already been split into an array at '_'s and called table_split

                        note that the selections made by each command will return an array of strings. that should be joined by _s. 
                        You should check that  it's an array. and not just a single string. 
                        If it's a string. don't join it. 

                        ___filters___ is a list of things each type needs in order to be considered. part of that type. 
                        i.e. data needs to have at least 4 parts. type, phase, respondent, instrument. 
                        If it doesn't then it's some kind of special meta-data. like data_dates..... 
                        And we don't know what to do with them yet. 

                        -----
                            you should be aware. that type should always be the first secgment of any tablename in the wtp database. 
                            we use that to select which types to try. but first we filter it. if it doesn't match the filter's criteria it's categorized as misc. 
                        ----
                            If you start updating this filter you'll need to update get_table_type as well. 

                        """
            }

        attributes_dict = {}
        tablename = row[2] # the pypyodbc tables() row has tablename at index 2
        
        if(debug):print('Parsing table %s' % tablename)
        table_split = tablename.split('_') # the sections should be split by _
        table_type = self.get_table_type(table_split, tablename_maps['filters'])
        if(debug):print('type determined to be %s' % table_type)

        for attrib in tablename_maps['parsing maps'][table_type]:
            parts = eval(tablename_maps['parsing maps'][table_type][attrib])
            if(type(parts) is list):
                parts = '_'.join(parts)
            attributes_dict[attrib] = parts
        attributes_dict['type'] = table_type
        
        if(debug):
            print('\tbecame->\n\t' + u.prettify_str(attributes_dict).replace('\n','\n\t'))
        
        return attributes_dict

    def get_table_type(self, table_split, filters): # find what type of table this is
        """ This determines the filter type based on the tablename and the filters map. 
            """

        if(table_split[0] not in filters):
            return 'misc'
        for aspect in filters[table_split[0]]: # go through each aspect within
            #####################
            if(aspect is 'length'):
                """ Make sure length is at least this... """
                if(table_split.__len__() < filters[table_split[0]][aspect]):
                    return 'misc'
            #####################
            if(aspect is 'disallowed words'):
                """ Check no dissallowed words are in the tablename """
                for word in filters[table_split[0]][aspect]:
                    if(word in table_split):
                        return 'misc'
            #####################
        # if passed all tests. return type. 
        return table_split[0]

    ################
    ## END PARSING



class dbImporter:

    def __init__(self, tables_not_to_include = [], debug = True, debugMore=True):
            
        mm = MapManager(debug=False)   #initialize the map manager
        if(debug): mm.log_mappings('logs/mappings_used') #check that mappigs are correct

        es_struct={} # begin populating a struct in the fashion we want the es to be in. 
            # NOTE: the keys will be tablenames. 

        dbm = dbManager()   #initialize database Manager

            # open the database and enumerate through tablenames
        for i,tablename in enumerate(dbm.open_db()):
            if(tablename not in tables_not_to_include):
                    #break the tablename into it's individual parts. 
                table_info_raw = dbm.parse_row(tablename, debug = debug) 
            
                    # apply the mapping based on those parts. save them to the struct. 
                table_info_raw = mm.apply_mapping(table_info_raw, debug = debug) 
                
                # if there is an instrument... get the scales.
                if('instrument abbreviation' in table_info_raw):
                    if(debugMore): print('\n\nAbout to look at scales for %s' % u.prettify_str(table_info_raw))  
    
                    # get the scales & instrument name from the mappings
                    scales, instrument_name = mm.get_info(table_info_raw['instrument abbreviation'], debug = debugMore)
                    
                    if(scales): # get_info may return null, if it doesn't have scales/instrument name
                        table_info_raw['scales'] = scales
                    if(instrument_name):
                        table_info_raw['instrument name'] = instrument_name
    
                            #table_info_raw WILL have a tablename.
                es_struct[table_info_raw['tablename']] = table_info_raw

        u.log_file('logs/struct_uploaded.json', \
                            message = u.prettify_str(es_struct))
        dbm.close_db()

        dbm.open_es()                       
        dbm.insert_struct_to_es(es_struct, 'tables') 
        #dbm.close_es()                             #may be unsafe.


        # dbm.insert_struct_to_es(table_info_raw,table_info_ras['tablename'])

importer = dbImporter()
