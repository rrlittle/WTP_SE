""" 
This is the readme for this dict. This dict defines the parameters for 
                the WTP naming conventions. 
                        This has 3 sections. 
                            - This readme
                            - Parsing maps
                            - Filters

                        ___This readme___ is self explanatory.

                        ___Parsing maps___ has a bunch of commands to parse a tablename into various attributes.
                            the structure is like so:
                                type{
                                    'attribute this type should have 1'
                                    'attribute this type should have 2'
                                    etc. 
                                }
                            It is assumed that the tablename has already been split into an array at '_'s and called table_split

                        note that the selections made by each command will return an array of strings. that should be joined by _s. 
                        You should check that  it's an array. and not just a single string. 
                        If it's a string. don't join it. 

                        ___filters___ is a list of things each type needs in order to be considered. part of that type. 
                        i.e. data needs to have at least 4 parts. type, phase, respondent, instrument. 
                        If it doesn't then it's some kind of special meta-data. like data_dates..... 
                        And we don't know what to do with them yet. 

                        -----
                            you should be aware. that type should always be the first secgment of any tablename in the wtp database. 
                            we use that to select which types to try. but first we filter it. if it doesn't match the filter's criteria it's categorized as misc. 
                        ----
                            If you start updating this filter you'll need to update get_table_type as well. 

                        """

def minLength(table_split, length):
    """return True if table_split is at least len long
        recall true allows table to pass this filter"""
    return len(table_split) >= length
def ensureTheseWordsArentThere(table_split, wordList):
    """ fails if any of the words in wordlist are found in 
        table_split"""
    for w in wordList:
        if w in table_split: return False
    return True


parsing_maps = {
                 'data':{
                     'tablename':'table_split[0:]',
                     'phase':'table_split[1: 2]',
                     'instrument abbreviation':'table_split[2 : table_split.__len__()-1]',
                     'respondent':'table_split[-1]',
                 },
                 'calc':{
                     'tablename':'table_split[0:]',
                     'phase':'table_split[1: 2]',
                     'instrument abbreviation':'table_split[2: table_split.__len__()-1]',
                     'respondent':'table_split[-1]',
                     },
                 'misc':{
                     'tablename':'table_split[0:]',
                     }
            }

filters = {
                'data':{
                    'length':4,
                    'disallowed words':[
                        'dates'
                    ]
                },
                'calc':{
                   'length':4,
                    'disallowed words':[
                        'dates'
                    ]
                }
            }           

filtering_functions = {
    'length': minLength,
    'disallowed words': ensureTheseWordsArentThere
}