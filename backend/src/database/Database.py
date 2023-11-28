from pyArango.connection import Connection
import os
import json
from arango import ArangoClient
import cag.utils.config as graph_config
from pyArango.connection import Connection
import time

from database.EOGraphCreator import EOGraphCreator


def get_connection(username:str, password:str, arangoURL:str):
    '''
        Get ArangoDB connection
        Retry to establish connection for #retries times 
    '''
    retries = 5
    for i in range(retries):
        try:
            conn = Connection(
                username=username, 
                password=password, 
                arangoURL=arangoURL
            )
            return conn
        except Exception as e:
            print(f"failed to establish ArangoDB connection... (try {i})")
            print(e)
            if i+1==retries:
                print(f"Maximum tries exceeded... Shutting down")
                return None
            
            print(f"Go to sleep and try again tomorrow...")
            time.sleep(5)
            print(f"Trying again to establish connection... (try {i+1})")


def init_db(hostURL:str, username:str, password:str, db_name:str, graph_name:str, data_path:str):
    '''
        Initializes the database with json files from arangodump and builds the graph
        Note: this function assumes that the database is empty but that it already exists
    '''

    client = ArangoClient(hosts=hostURL)
    db = client.db(db_name, username=username, password=password)

    print("Starting to populate database with node collections...")
    # create node collections
    node_directory = f"{data_path}/nodes"
    edge_directory = f"{data_path}/edges"
    for filename in os.listdir(node_directory):
        file_path = os.path.join(node_directory, filename)
        # check if file is a json file
        if filename.endswith(".json") and os.path.isfile(file_path):
            # process the file here
            collection_name = filename.split(".")[0]
        if not db.has_collection(collection_name):
            collection = db.create_collection(collection_name, edge=False)
        else:
            collection = db.collection(collection_name)
        print(f"processing file {filename} (collection name {collection_name})")
        with open(file_path, 'r') as file:
            doc_list = json.load(file)
            print(f"found {len(doc_list)} documents")
            for doc in doc_list:
                # create document and save it in the collection
                collection.insert(doc)

    print("Finshed populating node collections...")
    print("Start to populate edge collections...")
    for filename in os.listdir(edge_directory):
        file_path = os.path.join(edge_directory, filename)
        # check if file is a json file
        if filename.endswith(".json") and os.path.isfile(file_path):
            # process the file here
            collection_name = filename.split(".")[0]
        if not db.has_collection(collection_name):
            collection = db.create_collection(collection_name, edge=True)
        else:
            collection = db.collection(collection_name)
        print(f"Processing file {filename} (Collection name: {collection_name})")
        with open(file_path, 'r') as file:
            doc_list = json.load(file)
            print(f"Found {len(doc_list)} documents")
            for doc in doc_list:
                # create document and save it in the collection
                collection.insert(doc)
    
    print("Finished populating database with edge collections...")

    print("Starting to create graph...")
    init_graph(hostURL, username, password, db_name, graph_name)
    print("Finsihed creating graph...")

def init_graph(hostURL:str, username:str, password:str, db_name:str, graph_name:str):
    cag_config = graph_config.Config(
        url=hostURL, 
        user=username, 
        password=password, 
        database=db_name, 
        graph=graph_name
    )

    # create graph
    gc = EOGraphCreator(
        None, 
        cag_config, 
        initialize=True, 
        load_generic_graph=False
    )

    # create search views
    gc.create_search_views()

