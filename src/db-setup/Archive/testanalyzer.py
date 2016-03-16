print("""   

    """)
body =  {
            'settings': {
                'analysis': {
                    'analyzer': {
                        # custom analyzer for analyzing file paths
                        'myngramanalyzer': {
                            'tokenizer': 'myngramtokenizer',
                        }
                    },
                    'tokenizer':{
                        'myngramtokenizer':{
                            'type':'nGram',
                            'token_chars' : ['whitespace']
                        }
                    }
                }
            }
        }
index = 'testindex'

from elasticsearch import Elasticsearch as es
e = es()
e.indices.create(
    index = index, 
    body = body,
    )