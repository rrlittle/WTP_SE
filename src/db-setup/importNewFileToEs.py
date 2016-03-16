
""" This script will prompt you for a file to upload 
    and upload it. it should be run from thurios so that all the defaults work
    """
from db2es import db2es as db


def run():
    c = db.Controller()
    bulk_file = c.calculate_bulk_upload_for_all_tables(log=c.log)
    if bulk_file:
        c.upload_bulk_file(bulk_file, refresh=True)

if __name__ == '__main__':
    run()