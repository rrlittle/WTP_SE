"""
    """
from .waisman_utils import prettify_str, open_db_con, load_py_module
from os.path import join
import logging


class dbManager:

    def __init__(self, 
        db_con_str = 'DSN=wtp_data', 
        path_to_defs = ['staticallyDefined', 'parsingRules.py'],
        log = logging ):
        """ 
            """
        defsFile = None 
        try:
            defsFile = load_py_module(join(*path_to_defs))
        except IndentationError as e: # a syntax error
            raise parsingRuleSyntaxError(e) 

        ### assert that it's following all the rules
        self.maps = defsFile.parsing_maps
        self.filters = defsFile.filters
        self.filtering_functions = defsFile.filtering_functions
        
        self.db_con_str = db_con_str # open and close db connections as needed. 
                                    # I'm not sure how garbage collection works
                                    # it seems __del__ is unreliable

              
    def get_tablenames(self):
        """ returns a list of tablenames from the database """
        con = open_db_con(self.db_con_str)
        cur = con.cursor()
        tables = cur.tables 
        tables =  [t[2] for t in tables]
        cur.close()
        return tables

    def parse_tablename(self, tablename, log=logging):
        """ This function breaks up the tablename based on the WTP conventions
                (i.e. sections are seperated by `_`) and the rules provided by
                the file are path_to_defs during __init__. 

                After breaking up the tablename into as many pieces as we can 
                without any outside information it's returned as a dictionary.

                The information to be returned should be defined in 
                self.maps loaded from the defs file during 
                __init__. 
            """
        attrib_dict = {}

        log.debug('parsing table %s'%tablename)

        table_split = tablename.split('_') # ASSUMING SECTIONS SPLIT by _  
        table_type = self.get_table_type(table_split)

        attrib_dict['type'] = table_type
        log.debug('type determined to be %s'%table_type)

        for attrib in self.maps[table_type]:
            parts  = eval(self.maps[table_type][attrib])
            if type(parts) is list: # it could be a string, in which case..
                parts = '_'.join(parts) # we don't want to join them with `_`
            attrib_dict[attrib] = parts

        log.debug('\t expanded to -> \n\t%s'\
            %prettify_str(attrib_dict).replace('\n','\n\t'))
        return attrib_dict

    def get_table_type(self, table_split, log = logging):
        """ This function determines the most likely type of this table based 
            on the components of table_split. basically it should be 
            table_split[0] unless it doesn't match. This is WTP convention

            This function relies on the filters defined in parsing rules.
            filters should be a dictionary with various types defined as keys.
            these are the types this function can produce. 

            parsingRules.fileters & parsingRules.filtering_functions
            ------------
                the values to each of these keys should be a dictionary of filters.
                the filter keys should also be found in filtering functions 
                (a dictionary that maps the filtering functions to the actual 
                    function objects)
                The filtering functions should take 2 positional arguments,
                    1. table_split
                    2. the value from the filter (within filters dictionary)
                and return True of False
    
                e.g. the following should be in parsing rules file.
                filters = {
                    'type1':{
                        "filter1":{arg1:1,arg2:2},
                        "filter2":3
                    }
                }
                filtering_functions = {
                    "filter1":foo1,
                    "filter2":foo2
                }
                def foo1(table_split, arg): return True
                def foo2(table_split, arg): return False
    
                This will say that if table_split is type1, it will pass through
                    both filters 1 & 2. i.e. filter1 and filter 2 will return true, 
                    as in, table_split should pass  

            args:
                table_split: the table name split by `_`.

            """

        if table_split[0] not in self.filters:
            log.debug('%s did not match any known filters (%s) return misc'\
                %(table_split,  list(self.filters.keys())))            
            return 'misc'
        type = table_split[0]

        ### Check for any reason to exclude table from this type
        for aspect in self.filters[type]:
            # every parsingRules file should have filter_functions and filters
            # defined. they are loaded during __init__

            try:  # if function returns false, this table does not pass and returns misc
                if not self.filtering_functions[aspect](table_split, self.filters[type][aspect]):
                    return 'misc'
            except NameError as ne:
                log.error("Function %s does not exist in parsingRules file"%self.filtering_functions[aspect].__name__)
                log.error("Potential correction needed in filtering_functions mapping.")
                log.error(ne)
                raise parsingRuleSyntaxError() 
            except TypeError as te:
                log.error("The function definitions have wrong number of arguments.")
                log.error("Function should take only two arguments, first being table_split list and the second being argument.")
                log.error(te)
                raise parsingRuleSyntaxError()
            except KeyError as ke:
                log.error("The filter (eg.length) attribute does not have a mapped function in filtering_functions")
                raise parsingRuleSyntaxError()
        log.debug('returning type: %s'%type)
        return type





class parsingRuleSyntaxError(Exception):
    '''
        This exception is thrown when there is an error in parsing Rule script.

        The mapping in the filtering_functions may be wrong (OR)
        The function definition may be wrong.

    '''
    pass


class unitTest:
    def __init__(self):
        """ to do some teests on this file. just add them here. 
            we'll probably only do these manually.

            to run open a pyterm from outside this package run
            from db2es import dbManager
            dmManager.UnitTest() # and that should do it.
            """

        logging.basicConfig(level=logging.INFO)
        l = logging.getLogger(__name__)
        l.setLevel(logging.INFO)
        
        dm = dbManager(log = l)
        
        l.info('---------\n')
        tname = 'data_3_rdmr_agn_t'
        l.info('testing %s'%tname)
        type = dm.get_table_type(tname.split('_'))
        l.info('type = %s'%type)
        parsed = dm.parse_tablename(tname, log = l)
        l.info('results-> \n%s'%prettify_str(parsed))
        l.info('---------\n')

        tname = 'calc_3_agn_fdsf_fds_t'
        l.info('testing %s'%tname)
        type = dm.get_table_type(tname.split('_'))
        l.info('type = %s'%type)
        parsed = dm.parse_tablename(tname, log = l)
        l.info('results-> \n%s'%prettify_str(parsed))

        l.info('---------\n')
        tname = 'data_3_dates'
        l.info('testing %s'%tname)
        type = dm.get_table_type(tname.split('_'))
        l.info('type = %s'%type)
        parsed = dm.parse_tablename(tname, log = l)
        l.info('results-> \n%s'%prettify_str(parsed))

