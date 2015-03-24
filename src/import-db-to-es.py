'''
This script is to import the WTP database into Elastic Search in a predescribed way. 
This will not delete anything, so If you want to refresh the db completely, be sure to 
delete the directories in the Elastic Search working folder. 

The structure it will buld the db to is thus:
indices:{  // indices is an ES keyword the db is organized primarily by index, then types, then document id. 
	"meta-data" : {
		"*types*" : {		// types is an ES keyword. I'm just representing it as a json key, cause it makes sense. 
			"data":{
				"*documents*":{
					"id1":{
						"table name":
						"phase":
						"respondent":
						"study abreviation":
						"size": // i.e. number of participants/rows

						"scales": [] 
						"errors":
						"comments":
						"repeats?": // yes/no
						"final dataset?": // yes/no
					},
					"id2":{
						"table name":
						"phase":
						"respondent":
						"study abreviation":
						"size": // i.e. number of participants/rows

						"scales": [] 
						"errors":
						"comments":
						"repeats?": // yes/no
						"final dataset?": // yes/no
					}
				} // end meta-data/data/documents
			}, 	// end meta-data/data
			"calcs":{
				"*documents*":{
					"id1":{
						"table name":
						"phase":
						"respondent":
					}
				}
			},	// end meta-data/calcs
			"dates":{
				"*documents*":{
					"*id1*":{
						"tablename":
					}
				}
			},
			"unused":{
				"*documents*":{
					"id1":{
						"tablename":
					}
				}
			}	// end meta-data/unused
		}// end meta-data/types
	}, // end meta-data
	"documents":{
		"id1":{
			"document object":
			"size":
			"title":
			"tags":[] 
		}
	}
}

You should be able to interact with a specific id via curl using "get /index/type/id." e.g. "get /meta-data/calcs/3" will be the third document in calcs, within the index meta-data.

checklist of things to do.
connect to database:
parse tables:
upload them:
'''
import pypyodbc as db
import waisman_utils as u
import pprint as p
from elasticsearch import Elasticsearch as es 



def main():
	# open db connection
	cur = u.open_db_con()
	
	# get data tables, calc tables, and extra tables from db
	tablenames = get_tables(cur)
		# => data tables{tablename,phase,respondent,study abrv, respondents, scales}

	#parse table names
	es_struct= {} # the es stores files in a dictionary like structure. this is how we will represent them here. 
	es_struct['meta_data'] = extract_meta_data(tablenames, cur)
			#meta-data = data, calc, and misc tables

	#insert data tables data into es. 
	insert_to_es(es_struct)


####################################
######################################
## inserting to ES
######################################
def insert_to_es(struct):
	e = es()
	for index in struct: #outer level of struct is indexes for the db
		for doc_type in struct[index]: # inner level are individual docs
			for doc in struct[index][doc_type]: #each of these is an individual table, which will be a single document in the db
				x = e.index(index=index, doc_type=doc_type, body=struct[index][doc_type][doc])
				print(x)


		


####################################
######################################
## Extracting data
######################################
def extract_meta_data(tables, cur):
	"""This function is responsible for constructing the meta_data dictionary of the es structure
		e.g. this stuff:
		"meta-data" : {
		"*types*" : {	 
			"data":{
					tablename{ //id1
						"table name","phase","respondent","study abreviation","size","errors","comments","repeats?","final dataset?","scales": []
					}
			}, 	// end meta-data/data
			"calcs":{
				"tablename"{ //id1
					"table name","phase","respondent", "study abreviation"
				}
			},	// end meta-data/calcs
			"misc":{
				"tablename: { //id1
					"tablename":
				}					
			}	// end meta-data/unused
		}// end meta-data/types
	} // end meta-data
	
	It does this by abstracting methods for getting each element. 
	
	These methods are available:
	- tablename, available fro data tables
	- phase, available fro data tables
	- study abreviation, available for data and calc tables
	- respondent, available for data and calc tables

	they all take the list of tabel, the db cursor, and the dictionary of 
	
	ASSUMPTIONS:
	-----------------
	 Table names can be in this form, and there are no others.  
	 		"calc"/"data"_phase_study-with-underscores_respondent


		'data':{"table" ,"name","phase","respondent","study abreviation","size","errors","comments","repeats?","final dataset?","scales"},
	"""
	#keys to include for each:
	docs_by_type = {
		'data':[tablename,phase,respondent, study_abreviation],
		'calc':[tablename,phase,respondent, study_abreviation],
		'misc':[tablename]
	}

	types = {} # es calls each sub index a type. So that's what I'm a calling them
	for typ in tables:  # for each type in tables which has data, calc, misc ...
		if typ in docs_by_type: #if that type is represented in docs by type
			for doc in docs_by_type[typ]: # do all the methods represented for that type in docs_by_type.  
				if(typ not in types.keys()):
						types[typ] = {}
				doc(tables[typ], cur, types[typ]) #returns a dict of dicts. one per tablename. each containing things specified by docs_by_type
	
	#p.pprint(types)
	return types

def tablename(tablenames, cur, type_list):
	for t in tablenames:
		if(t not in type_list.keys()):
			type_list[t] = {}
		type_list[t]["tablename"] = t

def phase(tablenames, cur, type_list):
	for t in tablenames:
		if(t not in type_list.keys()):
			type_list[t] = {}
		type_list[t]['phase'] = t.split('_')[1] 

def respondent(tablenames, cur, type_list):
	for t in tablenames:
		if(t not in type_list.keys()):
			type_list[t] = {}
		type_list[t]['respondent'] = t.split('_')[-1] 

def study_abreviation(tablenames, cur, type_list):
	for t in tablenames: 
		if(t not in type_list.keys()):
			type_list[t] = {}
		s = t.split("_")
		s.remove(s[-1])
		type_list[t]['study_abreviation'] = ("_".join(s[1:]))
		#assuming study is everything except data, phase and respondent. 
		# we can further parse it when we have the naming conventions up and running.


####################################
######################################
## getting data from db
######################################
def get_tables(cur):
	tables = [t[2] for t in cur.tables()] 	#each table is an array of meta-data, index 2 is the tablename
	
	table_types = {}
	filters = ['data', 'calc']
	for f in filters:
		table_types[f] = [t for i,t in enumerate(tables) if t.startswith(f)]
	table_types['misc'] = [t for i,t in enumerate(tables) if not t.startswith(tuple(filters))]

	
		# for debugging purposes 	
	#for t in tables:
	#	if(t not in table_types['data'] and t not in table_types['calc'] and t not in table_types['misc']):
	#		print(t)

	print(table_types.keys())
	print(len(tables), 'all tables')
	print(len(table_types['misc']), "misc")
	print(len(table_types['calc']), "calc")
	print(len(table_types['data']), "data")	

	return table_types


main()