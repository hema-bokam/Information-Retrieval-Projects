import json
import os
import pysolr
import requests
import pandas as pd

CORE_NAME = "IR24P3"
VM_IP = "34.85.223.192"

def delete_core(core=CORE_NAME):
    print(os.system('sudo su - solr -c "/opt/solr/bin/solr delete -c {core}"'.format(core=core)))


def create_core(core=CORE_NAME):
    print(os.system(
        'sudo su - solr -c "/opt/solr/bin/solr create -c {core} -n data_driven_schema_configs"'.format(
            core=core)))
    

class Indexer:
    def __init__(self):
        self.solr_url = f'http://{VM_IP}:8983/solr/'
        self.connection = pysolr.Solr(self.solr_url + CORE_NAME, always_commit=True, timeout=5000000)

    def do_initial_setup(self):
        delete_core()
        create_core()

    def create_documents(self, docs):
        print(self.connection.add(docs))
        
    def search_documents(self, topic):
        query = f'topic:"{topic}"'
        print(f"Searching for topic: {topic}")
        results = self.connection.search(query)
        for result in results:
            print(f"Title: {result.get('title')}")
            print("")
        print("done searching")
        return results
    
    def add_fields(self):
        data = {
            "add-field": [
                {
                    "name": "title",
                    "type": "string",
                    "indexed": True,
                    "multiValued": False
                },
                {
                    "name": "revision_id",
                    "type": "string",
                    "multiValued": False
                },
                {
                    "name": "summary",
                    "type": "text_en",
                    "indexed": True,
                    "multiValued": False
                },
                {
                    "name": "url",
                    "type": "string",
                    "multiValued": False
                },
                {
                    "name": "topic",
                    "type": "string",
                    "indexed": True,
                    "multiValued": False
                }
            ]
        }

        print("Sending request to:", self.solr_url + CORE_NAME + "/schema")
        response = requests.post(self.solr_url + CORE_NAME + "/schema", json=data)

with open('data/all_documents.json', 'r') as json_file:
    data = json.load(json_file)

df = pd.DataFrame(data)
# Setup Indexer
i = Indexer()
i.do_initial_setup()
i.add_fields()
collection = df.to_dict('records')
i.create_documents(collection)