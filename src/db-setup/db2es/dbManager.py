""" This file contains the functions responsible for
    doing database things. 

    such as getting all the tablenames, parsing the tablenames according
    to WTP conventions. 
    """
from .waisman_utils import prettify_str, open_db_con, load_py_module, db
from os.path import join 
import logging
import numpy as np

class dbManager:

    def __init__(self, 
        db_con_str = 'DSN=wtp_data', 
        path_to_defs = ['staticallyDefined', 'parsingRules.py'],
        log = logging ):
        """ this opbject deals with getting stuff from the database. 
            it's an object so that you can connect different objects 
            to different databases or use different parsing rules.

            db_con_str should be a string used by pypyodbc to connect to 
            a system DSN. 

            path_to_defs should be a os.path.join - able list to the parsing 
            rules python file.
            the rules file should be like the example in staticallyDefined 

            it should include parsing_maps, filters and filtering functions.
            look at the example file for more information.

            
            Each settings file should be named after the tablename that it maps to.  
            and contain a list of column names that should be included in the calculation. 
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
            
    def get_data(self, table, columns):
        ''' basically does "select" ','.join(columns) "from table"
            columns is a list of strings
            '''
        if len(columns) < 1:
            return [[]]
        sqlselect = ','.join(columns)
        con = open_db_con(self.db_con_str)
        cur = con.cursor()
        cur.execute('SELECT %s from %s'%(sqlselect, table))
        rows = [r for r in cur]
        cur.close()
        con.close()
        return rows
    def get_columns(self, table, types = False, log=logging):
        ''' returns a list of column names for this table or None
            if whole:  all data returned by cursor is returned
            else:       only column names
            '''
        con = open_db_con(self.db_con_str)
        cur = con.cursor()
        cur.execute('select * from %s'%table)
        desc = cur.description
        cols = [d[0] for d in desc]
        types_list = [d[1] for d in desc] # types are at 1
        cur.close()
        con.close()
        if types: return cols, types_list
        else: 
            return cols # column names are at 3
    
    def get_tablenames(self):
        """ returns a list of tablenames from the database """
        con = open_db_con(self.db_con_str)
        cur = con.cursor()
        tables = cur.tables()
        tables =  [t[2] for t in tables]
        cur.close()
        con.close()
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
            spaceless_attrib = attrib.replace(' ', '_')
            parts  = eval(self.maps[table_type][attrib])
            if type(parts) is list: # it could be a string, in which case..
                parts = '_'.join(parts) # we don't want to join them with `_`
            attrib_dict[spaceless_attrib] = parts

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
            except KeyError:
                log.error("The filter (eg.length) attribute does not have a mapped function in filtering_functions")
                raise parsingRuleSyntaxError()
        log.debug('returning type: %s'%type)
        return type

    def calc_num_respondents(self, tablename, log = logging):
        """ This function calculates the number of respondents in the given 
            table. 
            This is a safe function unless there's a connection problem of 
            some kind. If it can't be calculated for whatever reason it will 
            return None, else a positive integer that is the number of 
            respondents.

            ARGS: 
                tablename: the name of the table to compute

            This function determines the true unique respondents based on the 
            keys for the table and the count of those will be returned, this 
            should work for all tables. if the table exists
            """
        con = open_db_con(self.db_con_str)
        cur = con.cursor()
        sqlstmnt = "SELECT COUNT(*) FROM `%s`"%tablename
        count = None
        try:
            cur.execute(sqlstmnt)
            responses = [r for r in cur] # creates a set 
            countrow = responses[0] # selects first index, only one row responds.
            count = countrow[0] # only one column in row
        except db.Error as e:
            log.warning('Error counting resonses in %s : %s'%(tablename, str(e)))
            return None

        finally:
            cur.close()
            con.close()
        return count

    def get_keys(self, tablename):
        """ this returns a list of column names from 'tablename' 
            the names returned will be the primary keys of the table explicitly 
            set in the SQL CREATE STATEMENT, not assumed keys as some table seem
            to use in WTP... :( 
            """
        con = open_db_con(self.db_con_str)
        cur = con.cursor()
        keys = None
        try:
            cur.primaryKeys(tablename)
            keys = [k[3] for k in cur]
        except db.Error:
            return None
        finally:
            cur.close()
            con.close()
        
        return keys

    def get_scale_columns(self, tablename, scale_abbr, instr_abbr = None, log=logging):
        ''' this returns either the column names of a table that match 
            the wtp convention for columns with scales

            i.e. if a table has columns they should be identifiable via 
                the column name. it should be something like 
                bppa001t where the first 2 chars are instrument abbrev
                and the second 2 are  scale abbreviation. 

                However. I can't be sure how well tables follow that convention.

                for now this funtion will not use instr_abbr and just try and 
                find columns with scale_abbr in them
            '''
        cols, types = self.get_columns(tablename, types = True,log=log)
        ret_cols = []
        ret_types = []
        for i,col in enumerate(cols):
            if scale_abbr in col:   
                ret_cols.append(col)
                ret_types.append(types[i])
        log.debug('found these columns for %s(%s): %s'%(tablename, scale_abbr, ret_cols))
        return ret_cols, ret_types

    def calculate_chronbach(self, table, columns, col_types, 
        rev_columns = [], 
        log = logging,
        show_data = False,
        **kwargs):
        ''' this is given everything to calculate chronbachs alpha
            for these columns. 
            this selects the data from the provided columns for the table

            if any columns in the arg columns are also present in rev_columns
            the selections will be reversed. 
            '''
        log.debug('NEED TO REVERSE COLUMNS HERE! We are not doing that now.')
        data = self.get_data(table, columns)
        if len(data) == 0:
            log.info('No data in this table')
            return 9998

        # clean the data. we can only work with numbers. 
        # so try and convert them to floats.
        bad_cols = []
        # special column names that are never included
        spec_cols = ['twin','familyid','datamode'] 
        for col in spec_cols:
            if col in columns: bad_cols.append(columns.index(col))

        if show_data:
            log.info('Before removing columns!!!!!!!!!')
            log.info('types:%s'%col_types)
            for i,row in enumerate(data):
                log.info('(%s[%s])%s'%(table, i, data[i]))
            log.info('%s rows in data'%len(data))
        
        for i, typ in enumerate(col_types):
            log.debug('checking column  %s. type is %s at index %s:%s'%(columns[i], typ, i,not (typ is float or typ is int)))
            if not (typ is float or typ is int):
                log.info('removing column %s'%i)
                bad_cols.append(i)


        log.info('removing columns %s'%bad_cols)
        
        for i in range(len(data)):
            data[i] = [dat for col,dat in enumerate(data[i]) if col not in bad_cols]
        log.info('calculating chronbachs for %s with data %s by %s'%(table, 
            len(data),len(data[0])))

        if show_data:
            log.info('After removing COLUMNS!!!!!')
            for i,row in enumerate(data):
                log.info('(%s[%s])%s'%(table, i, data[i]))

        c = 9998
        try:
            c = run_chronbach(data)
            if c is np.NaN:
                c = 9998
        except chronbachNotEnoughFields:
            log.warning('not enough columns provided for this scale. columns : %s'%columns)
        return c
        


class parsingRuleSyntaxError(Exception):
    '''
        This exception is thrown when there is an error in parsing Rule script.

        The mapping in the filtering_functions may be wrong (OR)
        The function definition may be wrong.

    ''' 
    pass
class chronbachNotEnoughFields(Exception):
    ''' if there is only one column 
        '''

class unitTest:
    def __init__(self):
        """ to do some teests on this file. just add them here. 
            we'll probably only do these manually.

            to run open a pyterm from outside this package run
            from db2es import dbManager
            dmManager.UnitTest() # and that should do it.
            """
        try:
            logging.basicConfig(level=logging.INFO)
            l = logging.getLogger(__name__)
            l.setLevel(logging.INFO)
            
            dm = dbManager(log = l)
            
            l.info('\n\n\n\n UnitTests for dbManager')

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
        
            l.info('---------\n')
            tname = 'calc_4_visit_age'
            l.info('testing %s'%tname)
            type = dm.get_table_type(tname.split('_'))
            l.info('type = %s'%type)
            parsed = dm.parse_tablename(tname, log = l)
            l.info('results-> \n%s'%prettify_str(parsed))

            l.info('-----------\n\tChecking count of false table')
            tname = 'sdflsakdjf;l'
            count = dm.calc_num_respondents(tname, log=l)
            l.info(count)
            l.info('SHould have been None')

            
            l.info('-------------\n\t Checking chronbachs alpha')
            data = [[4.00, 3.00, 4.00, 4.00],[4.00, 3.00, 3.00, 3.00],
                    [5.00, 5.00, 5.00, 4.00],[3.00, 4.00, 4.00, 5.00],
                    [3.00, 4.00, 3.00, 3.00],[3.00, 3.00, 2.00, 3.00],
                    [2.00, 3.00, 2.00, 2.00],[4.00, 5.00, 4.00, 5.00],
                    [4.00, 5.00, 3.00, 5.00],[5.00, 3.00, 3.00, 5.00],
                    [3.00, 2.00, 1.00, 4.00],[2.00, 3.00, 4.00, 3.00],
                    [3.00, 2.00, 2.00, 2.00],[3.00, 3.00, 4.00, 2.00],
                    [4.00, 4.00, 4.00, 3.00],[4.00, 4.00, 1.00, 4.00],
                    [2.00, 3.00, 3.00, 2.00],[2.00, 1.00, 1.00, 1.00],
                    [3.00, 2.00, 3.00, 3.00],[3.00, 4.00, 3.00, 3.00],
                    [3.00, 2.00, 3.00, 3.00],[5.00, 5.00, 4.00, 5.00],
                    [1.00, 4.00, 3.00, 4.00],[3.00, 3.00, 3.00, 3.00],
                    [3.00, 4.00, 3.00, 4.00],[1.00, 3.00, 3.00, 4.00],
                    [2.00, 2.00, 2.00, 1.00],[3.00, 4.00, 4.00, 4.00],
                    [4.00, 5.00, 5.00, 5.00],[5.00, 4.00, 4.00, 5.00],
                    [3.00, 3.00, 5.00, 4.00],[3.00, 3.00, 2.00, 1.00],
                    [2.00, 3.00, 3.00, 2.00],[3.00, 3.00, 2.00, 2.00],
                    [3.00, 4.00, 4.00, 5.00],[4.00, 3.00, 3.00, 4.00],
                    [4.00, 2.00, 2.00, 3.00],[4.00, 3.00, 4.00, 4.00],
                    [3.00, 1.00, 1.00, 3.00],[3.00, 3.00, 3.00, 3.00],
                    [2.00, 3.00, 3.00, 4.00],[2.00, 3.00, 3.00, 3.00],
                    [2.00, 4.00, 3.00, 4.00],[2.00, 3.00, 3.00, 2.00],
                    [3.00, 2.00, 4.00, 4.00],[3.00, 3.00, 3.00, 2.00],
                    [5.00, 4.00, 4.00, 4.00],[3.00, 4.00, 2.00, 3.00],
                    [5.00, 4.00, 5.00, 4.00],[4.00, 4.00, 3.00, 4.00],
                    [3.00, 4.00, 3.00, 2.00],[2.00, 2.00, 1.00, 2.00],
                    [3.00, 3.00, 2.00, 2.00],[5.00, 5.00, 4.00, 4.00],
                    [3.00, 3.00, 3.00, 3.00],[3.00, 4.00, 3.00, 4.00],
                    [5.00, 4.00, 4.00, 4.00],[3.00, 4.00, 4.00, 4.00],
                    [1.00, 2.00, 1.00, 2.00],[1.00, 1.00, 1.00, 1.00]]
            data = np.asarray(data)
            l.info('Data looks like %s'%str(data))

            calculted = run_chronbach(data)
            l.info('calculted alpha = %s. Should be .839'%str(calculted))


            l.info('-------------\n\t Checking Actual tables')
            table = 'data_1_bi_f'
            scale_abbr = 'co'
            scale_cols = dm.get_scale_columns(table, scale_abbr)
            actual_scale_cols = ['bico001f', 'bico005f','bico010f', 'bico013f',
                                'bico015f', 'bico019f','bico020f', 'bico022f',
                                'bico025f', 'bico029f','bico031f']
            l.info('should figure out the columsn of this table are:')
            for i in actual_scale_cols: l.info('\t%s'%i)
            l.info('calculated columns are:')
            for i in scale_cols: l.info('\t%s'%i)
            chronbach = dm.calculate_chronbach(table, scale_cols, log=l)
            l.info('chronbach was calculated to be %s'%str(chronbach))


            

            l.info('===================\n DONE')



        except Exception as e:
            print('%s error while running default dbManager'%e)

def run_chronbach(data):
    """ this computes a chronbachs alpha given a data matrix.
        this is using the R implementation by default. 

        α = Nc / (v + [N-1]*c)

        N : Number of items 
        c : average inter-item covariance among the items
        v : average variance

        where items is the number of cols in the data matrix

        this does not currently handle missing data...
        except for 9998 and 9999

        """

    itemscores = np.asarray(data,dtype=float) # turn it into a numpy array 
    
    itemvariance = itemscores.var(axis=0, ddof=1) 
                                # axis 0 is columns
                                # ddof 1 is the divisor used in calculation is
                                #   N -ddof
    totalvar = itemvariance.sum() # sum of all question variances

    tscores = itemscores.sum(axis=1) # sum the rows
    tscoresvar = tscores.var(ddof=1) # variance of tscores
    nitems = itemscores.shape[1] # num of cols (assuming this is not jagged)

    if nitems == 1:
        raise chronbachNotEnoughFields

    return ( nitems / float(nitems-1) ) * ( 1 - (totalvar / float(tscoresvar))) 