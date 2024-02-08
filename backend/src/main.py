from fastapi import FastAPI, Response
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import yaml
from pyArango.connection import Connection
from dotenv import load_dotenv
import os
from starlette.background import BackgroundTask



# add path to import queries
import sys
sys.path.append("src/")


from utils import get_stac_collection_from_id

from queries.Requests import *
from queries.QueryAnalyzer import QueryAnalyzer
from queries.DataRetriever import DataRetriever
from database.Database import init_db, get_connection




# LOAD CONFIG
with open('src/config.yml', 'r') as file:
    config = yaml.safe_load(file)
    arango_config = config['arango']
    frontend_config = config['frontend']

    web_api_key = config['web_api_key']
    geonames_username = config['geonames_username']
    web_api = config.get('web_api', 2) # default is Chatnoir (=2)

    arango_username = arango_config.get('username')
    arango_password = arango_config.get('password')
    arango_url = arango_config.get('hostURL')
    db_name = arango_config.get('database')
    graph_name = arango_config.get('graph')
    data_path = arango_config.get('data_path')

    frontend_url = frontend_config.get('hostURL')



# ESTABLISH ARANGODB CONNECTION
conn = get_connection(username=arango_username, password=arango_password, arangoURL=arango_url)
if conn is None:
    print(f"ERROR - COULD NOT ESTABLISH ARANGODB CONNECTION!")
    print(f"SHUTTING DOWN BACKEND SERVICE NOW")
    sys.exit()

# INIT DATABASE IF IT DOES NOT EXIST
if db_name not in conn.databases:
    conn.createDatabase(name=db_name)
    db = conn.databases[db_name]
    init_db(hostURL=arango_url, username=arango_username, password=arango_password, db_name=db_name, graph_name=graph_name, data_path=data_path)
else:
    db = conn.databases[db_name]

# CREATE BACKEND API 
app = FastAPI()


# CURRENTLY, CORS IS ENABLED FOR ALL ORIGINS (FOR DEVELOPMENT PURPOSES)
# origins = [
#     "http://localhost",
#     frontend_url, 
#     "http://localhost:8080", 
# ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# create QueryAnalyzer object
qa = QueryAnalyzer(geonames_username='johndolier')

# create DataRetriever object
data_retriever = DataRetriever(web_api_key=web_api_key, db_instance=db, graph_name=graph_name, web_api=web_api)

# DEFINE ENDPOINTS

@app.post("/pubRequest")
def pub_request(request: PubRequest) -> tuple[str, list[dict]]:
    try:
        results = data_retriever.make_publications_query(
            query=request.query, 
            keywords=request.keywords, 
            #limit=request.limit, 
        )
    except Exception as e:
        print(e)
        print(f"error - make_publications_query failed for request: {request}")
        results = []
    
    return ('publications', results)

@app.post("/stacCollectionRequest")
def stac_collection_request(request: STACCollectionRequest) -> tuple[str, list[dict]]:
    try:
        results = data_retriever.make_stac_collection_query(
            query=request.query, 
            keywords=request.keywords, 
            #limit=request.limit, 
        )
    except Exception as e:
        print(e)
        print(f"error - make_stac_collection_query failed for request: {request}")
        results = []
    
    return ('stac_collections', results)

@app.post("/webRequest")
def web_request(request: WebRequest) -> tuple[str, list[dict]]:
    try:
        results = data_retriever.make_web_query(query=request.query, limit=request.limit, location_filter=request.location_filter, verbose=True)
    except Exception as e:
        print(e)
        print(f"error - make_web_query failed for request: {request}")
        results = []
    
    return ('web_documents', results)

@app.get("/keywordRequest")
def get_all_keywords_request():
    try:
        keywords = data_retriever.get_all_keywords()
    except Exception as e:
        print(e)
        print(f"error - get_all_keywords failed")
        keywords = []
    
    return keywords

@app.get("/authorRequest")
def get_all_authors_request():
    try:
        authors = data_retriever.get_all_authors()
    except Exception as e:
        print(e)
        print(f"error - get_all_authors failed")
        authors = []
    
    return authors

@app.get("/eoNodeRequest")
def get_all_eo_nodes_request():
    try:
        eo_nodes = data_retriever.get_all_eo_nodes()
    except Exception as e:
        print(e)
        print(f"error - get_all_eo_nodes failed")
        eo_nodes = []
    
    return eo_nodes

@app.post("/graphQueryRequest")
def graph_query_request(request: GraphQueryRequest):
    try:
        results = data_retriever.make_graph_query(
            keywords_list=request.keywords, 
            authors_list=request.authors, 
            eo_list=request.eo_nodes, 
        )
    except Exception as e:
        print(e)
        print(f"error - make_graph_query failed for request: {request}")
        results = []
        
    return results

@app.post("/queryAnalyzerRequest")
def analyze_user_query(request: QueryAnalyzerRequest) -> dict:
    ''' 
        Takes the user query and extracts possible locations, time mentions and general keywords 
    '''
    try:
        analyzer_result = qa.analyze_query(user_query=request.query)
    except Exception as e:
        print(e)
        print(f"error - make_graph_query failed for request: {request}")
        # return empty "dummy" result
        analyzer_result = {
            'locations': [],
            'dates': [],
            'general_keywords': [],
        }
        
    return analyzer_result

@app.post("/stacItemRequest", status_code=200)
def make_stac_item_request(request: STACItemRequest, response: Response) -> tuple[str, list[dict]]:
    '''
        Makes a STAC request to retrieve items for the requested STAC collection (given location and time constraints)
    '''
    stac_collection_id = get_stac_collection_from_id(request.collection_id)
    if stac_collection_id is None:
        response.status_code = 400
        return ('stac_items', [])

    try:
        stac_items = data_retriever.make_stac_item_query(
            stac_collection_id=stac_collection_id, 
            location_filter=request.location_filter, 
            time_interval=request.time_interval, 
            limit=request.limit, 
        )
    except Exception as e:
        print(e)
        print(f"error - make_stac_item_query failed for request: {request}")
        stac_items = []
    
    return ('stac_items', stac_items)

@app.post("/notebookExportRequest", status_code=200)
def create_notebook_export(request: NotebookExportRequest, response: Response):
    ''' 
        Creates a jupyter notebook for export from the parameters of the request 
    '''
    stac_collection_id = get_stac_collection_from_id(request.collection_id)
    if stac_collection_id is None:
        response.status_code = 400
        return None
    
    try:
        filepath = data_retriever.create_notebook_export(
            stac_collection_id=stac_collection_id, 
            location_filter=request.location_filter, 
            time_interval=request.time_interval, 
        )
    except Exception as e:
        print(e)
        print(f"error - create_notebook_export failed for request {request}")
        filepath = None
    
    if filepath is None:
        print(f"something went wrong.. could not create python notebook for STAC download...")
        return None

    return FileResponse(filepath, media_type="ipynb", background=BackgroundTask(cleanup, filepath))


@app.post("/geotweetRequest")
def get_all_geotweets(request: GeotweetRequest):
    '''
        Debug / Exploration function to try out visualizing "geotweets" in the frontend application
    '''
    try:
        geotweets = data_retriever.get_geotweets(
            only_floods=request.only_floods, 
            limit = request.limit, 
        )
    except Exception as e:
        print(e)
        print(f"error - get_geotweets failed for request {request}")
        geotweets = []
    
    return geotweets



########################################
# HELPER FUNCTIONS
def cleanup(filepath):
    # remove file after sending response to client
    os.remove(filepath)
