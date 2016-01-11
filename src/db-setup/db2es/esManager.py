"""
	------------------------------------------------------------



	This package manages all the corresponding function of ES.

"""

from elasticsearch import Elasticsearch as es
from elasticsearch import helpers

class esManager:
	
	def __init__(self,hosts=[],**kwargs):
		open_es_conn(hosts,kwargs)

	def open_es_conn(self,hosts=[],**kwargs):
		'''
			This creates a default es object ( which establishes the connection to the ES )
			and returns the es object.
		'''
		
		if(len(hosts)==0):
			self.e = es()
		else:
			port=""
			if("port" in kwargs):
				port = kwargs["port"]
			else:
				port = 9200
			self.e = es(
			    hosts,
			    http_auth=('', ''),
			    port=port,
			    use_ssl=True,
			    verify_certs=False,
			    sniff_on_connection_fail=True
			)
		return self.e

	def close_es_conn():
		'''
			Elastic Search uses persistent connections and currently there is no way of closing connections.
			When the client is closed, it depends on the default garbage collector to close the socket.
		'''
		pass

	def bulk_insert(self, bulk_filePath=None, debug=True):
		'''
			Given a file with the syntax of bulk insert, this function calls the default es.bulk function 
			to insert all the rows to the ES database.

		'''
		bulk_fp = open(bulk_filePath)
        resp = self.e.bulk(bulk_fp.read())
        if debug: print(resp)







em = esManager()	
conn = em.open_es_conn(['localhost','6e3beff9.ngrok.com'])
conn.indices
