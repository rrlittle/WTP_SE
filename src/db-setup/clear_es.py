from db2es import esManager as es

def run():
    e = es.esManager()
    print(e.refresh())

if __name__ == '__main__':
    run()