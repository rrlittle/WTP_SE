from db2es import dbManager, mapManager, db2es


def mm():
    mapManager.unitTest()
def db():
    dbManager.unitTest()
def dbes(): 
    db2es.unitTest()

if __name__ == '__main__':
    db()
    