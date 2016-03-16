
""" This script will prompt you for a file to upload 
    and upload it. it should be run from thurios so that all the defaults work
    """
from db2es import db2es as db


def run():
    c = db.Controller()
    c.upload_bulk_file(db.getFilePathArr(), refresh=True, log=c.log)

if __name__ == '__main__':
    run()