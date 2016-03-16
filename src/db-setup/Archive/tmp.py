from db2es import db2es, mapManager

mapManager.unitTest()
db2es.unitTest()

print('\n\nunit tests for db2esController')
c = db2es.Controller()#esHosts=['6e3beff9.ngrok.com'])
outpath = c.calculate_bulk_upload_for_all_tables(mode='w')
if outpath:
    c.upload_bulk_file(bulkFilePath = outpath, refresh=True)
