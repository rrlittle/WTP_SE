"""
    ------------------------------------------------------------



    This package manages all the corresponding function of ES.

"""

from elasticsearch import Elasticsearch as es
import logging
from os.path import join


def open_es_conn(hosts=[], port=9200, **kwargs):
    '''
        This creates a default es object ( which establishes the connection to the ES )
        and returns the es object.

    '''
    
    if(len(hosts)==0):
        e = es()
    else:
        port=""
        if("port" in kwargs):
            port = kwargs["port"]
        else:
            port = 9200
        e = es(
            hosts,
            http_auth=('', ''),
            port=port,
            use_ssl=True,
            verify_certs=False,
            sniff_on_connection_fail=True
        )
    return e

def close_es_conn():
    '''
        Elastic Search uses persistent connections and currently there is no way of closing connections.
        When the client is closed, it depends on the default garbage collector to close the socket.
    '''
    pass


class esManager:
    def __init__(self,hosts=[],**kwargs):
        self.e = open_es_conn(hosts,kwargs)

    def bulk_insert(self, bulk_filePath, log = logging):
        '''
            Given a file with the syntax of bulk insert, this function calls the default es.bulk function 
            to insert all the rows to the ES database.
            ARGS:
                bulk_filePath = os.path.joinable list defineing path to bulk import file
                log = output stream
            RETURNS:
                es.bulk response or None if an error is thrown   
        '''
        try:
            bulk_fp = open(join(*bulk_filePath))
            resp = self.e.bulk(bulk_fp.read())
            log.debug(resp)
            return resp
        except Exception as e:
            log.critical('Error thrown in bulk import:  %s'%e)
            return None


    def refresh(self):
        """ remove all indices
            returns True iff deleting all indices was successful
             """
        return self.e.indices.delete('*')['acknowledged']



class UnitTest:
    """ to do some tests on this file. just add them here. 
            we'll probably only do these manually.

            to run open a pyterm from outside this package run
            from db2es import esManager
            esManager.UnitTest() # and that should do it.
        """
    def __init__(self):
        e = open_es_conn(hosts=['6e3beff9.ngrok.com'])
        print(e.cat.health())