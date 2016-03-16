""" This file is full to the gills of functions to actually
    do stuff with the goal of importing various datas and files and 
    calculations to Elastic search. 

    You'll have to discrminite which are helper functions and which are 
    higher level functions yourself. but  good hint would be to check out 
    the __init__ file of this package to see what's made available when you 
    import db2es thos are the main high level ones
    
    Db2EsController is an object that contains most of the functions
    I decided to make it a class because it is will need to create a 
    mapmanager as well as dbManager and esManager objects these all require some
    setup. and so with this being a class you can have multiple instances open
    with different setting if you need to say point to a different constructs 
    file or whatever. 
    """

import logging
from .dbManager import dbManager
from .esManager import esManager
from .mapManager import MapManager
from datetime import datetime as dt
import json
from os.path import join, split
from os import remove
import traceback
import sys
from tkinter import Tk
from tkinter.filedialog import askopenfilename
from .waisman_utils import get_logger
def format_scales(constructsScales):
    """ We store the scales differently in ES and in constructs.
        so we need to fix that at some point. 

        in ES. they are stored as a list of dicts with 2 
        keys. abbreviation and description

        in constructs they are stored as dicts. {abrev:description}
        """
    scales = []
    for abrv in constructsScales:
        scales.append({
            'abbreviation':abrv,
            'description' : constructsScales[abrv]
            })
    return scales

def getFilePathArr():
    """ opens ui to get file path for end users ease of use
        """
    Tk().withdraw()
    f = split(askopenfilename())
    return f


class Controller:
    """ This object is the main controlling device to make 
        """
    def __init__(self,
        esHosts = [],
        esPort = 9200,
        constructsPath = ['staticallyDefined', 'constructs.json'],
        parsingRulesPath = ['staticallyDefined', 'parsingRules.py'],
        db_con_str = 'DSN=wtp_data',
        log = None):

        if log is None:
            log = get_logger()
        self.log = log

            # defaults are set up for this application
        self.esm = esManager(hosts= esHosts, port=esPort) # doesnt' take log
        self.dbm = dbManager(path_to_defs = parsingRulesPath, log = log)
        self.mm = MapManager(constructsPath = constructsPath, log=log)

    def calculate_bulk_upload_for_all_tables(self, 
        tables_not_to_include = [],
        outFilePath = [
            'logs', 
            'bulk_upload_'+str(dt.now())[0:17].replace(" ","_").replace(":","_")
            ],
        esIndex = 'metadata',
        esType = 'tables',
        log = logging,
        mode='w+'):
        """ this calls self.calculate_bulk_upload_file, but for all tables in 
            the database.  
            """
        return self.calculate_bulk_upload_file(self.dbm.get_tablenames(),
            tables_not_to_include = tables_not_to_include,
            outFilePath = outFilePath,
            esIndex = esIndex,
            esType = esType,
            log = log, 
            mode = mode)

    def calculate_bulk_upload_file(self, 
        tables,
        tables_not_to_include = [], 
        outFilePath = [ 
            'logs', 
            'bulk_upload_'+str(dt.now())[0:17].replace(" ","_").replace(":","_")
            ],
        esIndex = 'metadata',
        esType = 'tables',
        log = logging,
        mode='w+', **kwargs):
        """ This goes about remaking the bulk upload file that is
            required for the esManager bulkUpload function.

            ARGS:
                tables = list of tablenames to compute
                tables_not_to_include = allows filtering out of unwanted tables
                outFilePath = joinable list of paths ending with the filename
                                by default filename if bulk_upload_now
                esIndex = the index for the elasticDatabase
                esType = the type for the elasticDatabase
                log = where to pipe output.
                mode = mode for updating the outfile. should be either
                        w (truncate existing file) or w+ (append to existing
                         file)  
            
            Note: this may produce important log information including
            """
        done = False
        outFile = join(*outFilePath)
        outFile_fp = open(outFile,mode)
        try:
            for i, tablename in enumerate(tables):
                log.info('Processing table %s/%s %s'%(i,len(tables),tablename))
                log.info('-  -  -  -  -  -  -  -  -  -  -  -')
                if tablename not in tables_not_to_include:
                    # this is not safe and can throw errors
                    actionDict,\
                    expanded_table_info = self.table_to_bulkimportItem(
                        tablename,
                        esIndex = esIndex, 
                        esType= esType,
                        log = log,**kwargs)         
                    json.dump(actionDict, outFile_fp)
                    outFile_fp.write('\n')
                    json.dump(expanded_table_info, outFile_fp)
                    outFile_fp.write('\n')
                    log.info('%s was successfully added to file!'%tablename)   
                    log.info('##############################################\n')

            done = True
        except Exception as e:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            log.fatal('The action could not be completed. '+
                'Error while processing %s. '% tablename )
            log.fatal('error:%s\n%s'%(e, traceback.format_exc()))
            log.fatal('---------------------------------------')

        finally:
            log.debug(done)
            outFile_fp.close()

        if not done: 
            log.fatal('deleting outfile.')
            remove(outFile)
            return None
        log.info('outfile finished!')
        return outFilePath

    def table_to_bulkimportItem(self, 
        tablename,
        esIndex='metadata', 
        esType='tables', 
        esId=None, 
        log = logging,**kwargs):
        """ this converts a tablename to a dictionary with all we know about 
            that table in it. 
            returns controldictionary, expanded_table_info
            """
        split_tablename_dict = self.dbm.parse_tablename(tablename, log=log)
        expanded_table_info = self.mm.apply_mapping(split_tablename_dict, 
                    log = logging)

        tmpRet = self.dbm.calc_num_respondents(tablename, log=log)
        if tmpRet: expanded_table_info['responses'] = str(tmpRet) 
                                        # set it as string
        

        if 'instrument_abbreviation' in expanded_table_info:
            matching_instruments = self.mm.get_scales_and_fullname(
                expanded_table_info['instrument_abbreviation'], log = log)

            # if we don't get a unique match
            if len(matching_instruments) != 1: 
                log.warning('__BadConstructsFile__: Got %s matches for abrv %s'%(
                    len(matching_instruments), 
                    expanded_table_info['instrument_abbreviation']  ))
            else:
                match = matching_instruments[0]
                if 'scales' in match: expanded_table_info['scales'] = format_scales(
                    match['scales'])
                if 'name' in match: expanded_table_info['instrument_name'] = \
                    match['name']
            
        # add chronbach info. this is a safe function. and won't add anything
        expanded_table_info = self.do_chronbach(expanded_table_info, log=log,**kwargs)
        actionDict = {  "index" : {}    }
        actionDict["index"]["_index"] = esIndex
        actionDict["index"]["_type"] = esType
        if esId:
            actionDict["index"]["_id"] = esId
        return actionDict,expanded_table_info

    def upload_bulk_file(self, bulkFilePath, refresh=False, log=logging):
        """ uploads data to es based using bulk api
            bulkFilePath os.path.joinable list defining path to 
            bulk import file

            refresh = T/F remove all indices before uploading data
            """
        if refresh: self.esm.refresh()
        return self.esm.bulk_insert(bulkFilePath, log=log)

    
    def do_chronbach(self, table_info, log=logging,**kwargs):
        """ This function sets up the chronbachs alpha for a table. 

            Chronbachs alpha is a measure of internal consistency for a given 
            instrument. 
            Each instrument is usually composed of a few different scales
            although some instruments may only have one. 
            
            this function goes through table_info and tries to calculate the 
            chronbach for each scale.

            ARGS & RETURN
            -----
            TABLE_INFO expects a dictionary as produced by 
            self.table_to_bulkimportItem which contains all we know about this 
            table.
            recall the structure is
            {
                ...
                ...
                "scales":[
                    {   'abbreviation':'abbrv',
                        'description':'desc'        }
                ]
            }

            RETURNS the same dictionary with the alphas calculated
            inserted with the key 'α'

            this is a safe funtion. i.e. it shouldn't throw any errors
            either fill in the table_info or not. check for 'alpha' within 
            scales to see what it did. 

            IMPLEMENTATION DEATAILS
            ------
            this function implements the following algorithm
            1. if 'scales' is not in table_info : do not proceed; else: continue
            2. for each scale:
                a. select all columns from the table that match wtp conventions 
                    for the current scale abbreviation
                    recall columns should be named: 
                            [instr_abbr][scale_abbr][quest_num][resp_abbr]
                b. calculate chronbachs alpha using subroutine described 
                    elsewhere using all the selected data. 

            """
        
        # check to make sure table_info has everything we need to continue. 
        if 'scales' not in table_info:
            log.debug('scales not found in table_info') 
            return table_info
        if 'tablename' not in table_info:
            log.warning('tablename not found in table_info. That is weird.')
            return table_info
        if 'type' not in table_info:
            log.warning('type not found in table_info. this is weird')
            return table_info

        if table_info['type'] != 'data':
            log.info('%s is not a data table. skipping chronbach'%table_info['tablename'])
            return table_info

        instr_abbr = None
        if 'instrument_abbreviation' in table_info:
            instr_abbr = table_info['instrument_abbreviation']

        tname = table_info['tablename']
        scales = table_info['scales'] # get list of scale dicts
        scale_abbrs = [sc['abbreviation'] for sc in scales] # get abbrevs

        log.info('Computing alphas for table %s'%table_info['tablename'])
        for i,scale in enumerate(scale_abbrs):
            log.info('calculating chronbach for %s (%s)'%(
                table_info['tablename'],scale))
            scale_cols, col_types = self.dbm.get_scale_columns(tname, scale, 
                                                instr_abbr = instr_abbr,log=log)
            log.info('%s (%s) including cols : %s'%(tname, scale, scale_cols))
            scale_alpha = self.dbm.calculate_chronbach(tname,
                                                        scale_cols,
                                                        col_types, 
                                                        log=log, 
                                                        **kwargs)
            log.info('alpha calculated to be %s'%str(scale_alpha))
            scales[i]['alpha'] = scale_alpha
        return table_info # should be filled in with alphas
            




class unitTest():
    """ to do some tests on this file. just add them here. 
            we'll probably only do these manually.

            to run open a pyterm from outside this package run
            from db2es import db2es
            db2es.UnitTest() # and that should do it.
         
        """
    def __init__(self):
        try:
            logging.basicConfig(level=logging.INFO)
            l = logging.getLogger('db2esDebugger')
            c = Controller(log = l)

            l.info('TESTING creating of individual BULK IMPORT concepts')

            l.info('\n------')
            tname = 'data_4_in_f'
            l.info('parsing table %s'%tname)
            com, info = c.table_to_bulkimportItem(tname,log=l)
            l.info(com)
            l.info(info)
            
            l.info('\n------')
            tname = 'data_4_hs_t'
            l.info('parsing table %s'%tname)
            com, info = c.table_to_bulkimportItem(tname,log=l)
            l.info(com)
            l.info(info)
            
            l.info('\n------')
            tname = 'data_sd_tb_m'
            l.info('parsing table %s'%tname)
            com, info = c.table_to_bulkimportItem(tname,log=l)
            l.info(com)
            l.info(info)


            l.info('\n------')
            tname = 'calc_c3_hb_m'
            l.info('parsing table %s'%tname)
            com, info = c.table_to_bulkimportItem(tname,log=l)
            l.info(com)
            l.info(info)

            l.info('TESTING CREATION of BULK IMPORT FILE')
            tnames = [
                'data_4_hs_t',
                'data_',
                'data_4_dates',
                'arch_1_de_m',
                'calc_4_visit_age',
                'calc_2_cd_f',
                'calc_sd_tb_m'
            ]
            #l.setLevel(logging.DEBUG)
            outPath = c.calculate_bulk_upload_file(tnames, 
                outFilePath=['logs','unitTestBulk.json'],
                log=l)

            outFp = open(join(*outPath),'r')
            for line in outFp.readlines():
                l.info(line)

        except Exception as e: 
            print('%s while running default db2es'%e)
