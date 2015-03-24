import pypyodbc as  db

def open_db_con():
	"""Opens Connection to wtp database
	returns: 
		cursor object from pypyodbc
	raises:
		some kind of exception to the tune of could not connect to db
		Unchecked.
	"""
	conn = db.connect('DSN=wtp_data')
	cur = conn.cursor()
	return cur

def close_db_con():
	"""Closes the connection to wtp database
		returns:
			nothing
		raises:
			nothing
	"""
	return
