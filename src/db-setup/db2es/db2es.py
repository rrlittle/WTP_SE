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
from dbManager import dbManager
from esManager import esManager
from mapManager import mapManager
import json
from datetime import datetime.now
from os.path import join

class Db2EsController:
    """ This object is the main controlling device to make 
        """
    def __init__(self, 
        constructspath = ['staticallyDefined', 'constructs.json'],
        parsingRulesPath = ['staticallyDefined', 'parsingRules.py']
        log = None):

        if not log:
            logging.basicConfig(level = logging.INFO)
            log = logging.getLogger(__name__)

        self.esm = esManager()
        self.dbm = dbManager(path_to_defs = parsingRulesPath, log = log)
        self.mm = MapManager(path = constructspath, log=log)

    def calculate_bulk_upload_file(self, 
        tables_not_to_include = [], 
        outFilePath = [ 
            'logs', 
            'bulk_upload_' + str(now()[0:]).replace(" ","_") 
            ], 
        log = logging ):
        """ This goes about remaking the bulk upload file that is
            required for the esManager bulkUpload function.
            """
        outFile = join(*outFilePath)
        outFile_fp = open(outFile,"w+")
        try:
            for i, tablename in enumerate(self.dbm.get_tablenames()):
                if tablename not in tables_not_to_include:
                # this is not safe and can throw errors
                actionDict, expanded_table_info = self.table_to_bulkimportItem()         
                json.dump(actionDict, outFile_fp)
                json.dump(expanded_table_info, outFile_fp)
                log.info('%s was successfully added to file!'%tablename)
            outFile_fp.close()
        except Exception as e: 
            log.fatal('The action could not be completed. '+
                'Error while processing %s.'% tablename + 
                'deleting outfile.')

    def table_to_bulkimportItem(self, 
        tablename,
        esIndex='metdadata', 
        esType='tables', 
        esId=None, 
        log = logging):
        """ this converts a tablename to a dictionary with all we know about 
            that table in it. 
            returns controldictionary, expanded_table_info
            """
        split_tablename_dict = self.dbm.parse_tablename(tablename, log=log)
        expanded_table_info = self.mm.apply_mapping(split_tablename_dict, 
                    log = logging)
        

        actionDict = {  "index" : {}    }
        actionDict["index"]["_index"] = esIndex
        actionDict["index"]["_type"] = esType
        if esId:
            actionDict["index"]["_id"] = esId
        return actionDict,expanded_table_info



                
