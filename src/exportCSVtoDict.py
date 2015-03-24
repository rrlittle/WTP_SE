############################################################
##By: Russell Little, Cherub Kumar
##Date: oct 2014
##
##
##This script will export data from a .csv file to json objects 
##that can be exported into elastic search.
##
## Specifically the CSV from the variable naming document (for the time being)
## We may modularize it later, once we have abetter idea of what we'll be importing
############################################################
import sys


print("Enter the document name to export. Don't include the extension. it should be csv.")
#filename = sys.stdin.readline().strip() + '.csv'
filename='variableNamingConventions_cleaned.csv'
try:
	f = open(filename, 'r')
except:
	raise OSError	
	print("that didin't work! You Suck!")

for line in f:
	try:
		print(f.readline())
	except:
		print("~~~~~~~~~~~~~~~~~~~~What's going on here?")
