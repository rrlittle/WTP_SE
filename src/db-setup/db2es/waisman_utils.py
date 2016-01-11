import pypyodbc as  db
import json
import importlib.util as imp


def load_json(path):
    f = open(path,'r')
    return json.load(f)


def load_py_module(path):
    spec = imp.spec_from_file_location('name', path)
    module = imp.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def open_db_con(conString):
    """Opens Connection to wtp database
    returns: 
        cursor object from pypyodbc
    raises:
        some kind of exception to the tune of could not connect to db
        Unchecked.
    """
    conn = db.connect(conString)
    return conn

def close_db_con():
    """Closes the connection to wtp database
        returns:
            nothing
        raises:
            nothing
    """
    return

def prettify_str(list_like, indent=2, sort_keys=True):
    """
    Returns a well formatted string with \\n and \\t so that it looks good. 
    Takes a list-like, serializable object
    you can also specify the indent, it defaults to 2

    Throws a TypeError if object is not serializable
    """
    try:
        return json.dumps(list_like, indent=indent, sort_keys = True)
    except:
        print('Cannot Serialize this object in wtp_utils.py prettify_str')
        raise TypeError

def log_file(path,message = None, keep_alive = False, mode='w'):
    """ Writes a string to a file, optionally specify mode. 
            'r' reading
            'w' writing
            'a' append to the end
            'b' binary mode
            ... etc. look at doc for open for more options. 
        """
    f = open(path, mode)
    written = 0
    if(message):
        written = f.write(message)
    if(keep_alive):
        return f
    else:
        f.close()
        return written


