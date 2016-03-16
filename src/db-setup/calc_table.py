from db2es import db2es as db


def run(table):
    c = db.Controller()
    actiondic,table_info = c.table_to_bulkimportItem(table,log=c.log, show_data=True)
    c.log.info('%s'%table_info)



if __name__ == '__main__':
    table = input('Enter a tablename to run \n>>>')
    run(table)