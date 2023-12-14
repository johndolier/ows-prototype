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
data_retriever = DataRetriever(web_api_key=web_api_key, db_instance=db, graph_name=graph_name)

# DEFINE ENDPOINTS

@app.post("/pubRequest")
def pub_request(request: PubRequest) -> tuple[str, list[dict]]:
    results = data_retriever.make_publications_query(
        query=request.query, 
        keywords=request.keywords, 
        #limit=request.limit, 
    )
    return ('publications', results)

@app.post("/stacCollectionRequest")
def stac_collection_request(request: STACCollectionRequest) -> tuple[str, list[dict]]:
    results = data_retriever.make_stac_collection_query(
        query=request.query, 
        keywords=request.keywords, 
        #limit=request.limit, 
    )
    return ('stac_collections', results)

@app.post("/webRequest")
def web_request(request: WebRequest) -> tuple[str, list[dict]]:
    results = data_retriever.make_web_query(query=request.query, limit=request.limit, verbose=True)
    return ('web_documents', results)

@app.get("/keywordRequest")
def get_all_keywords_request():
    keywords = data_retriever.get_all_keywords()
    return keywords

@app.post("/queryAnalyzerRequest")
def analyze_user_query(request: QueryAnalyzerRequest) -> dict:
    ''' Takes the user query and extracts possible locations, time mentions and general keywords '''
    analyzer_result = qa.analyze_query(user_query=request.query)
    #print(f"locations: {analyzer_result.get('locations')}")
    #print(f"dates: {analyzer_result.get('dates')}")
    #print(f"general keywords: {analyzer_result.get('general_keywords')}")
    return analyzer_result

@app.post("/geoparseRequest")
def get_location_from_user_query(request: GeoparseRequest) -> tuple[str, list]:
    ''' Extract locations and bboxes from user query if present '''
    geocoding_result = qa.get_location_and_geobounds_list(request.query)
    # TODO transform data for client? 

    return ('locations', geocoding_result)

@app.post("/stacItemRequest", status_code=200)
def make_stac_item_request(request: STACItemRequest, response: Response) -> tuple[str, list[dict]]:
    '''
        Makes a STAC request to retrieve items for the requested STAC collection (given location and time constraints)
    '''
    stac_collection_id = get_stac_collection_from_id(request.collection_id)
    if stac_collection_id is None:
        response.status_code = 400
        return None
    
    stac_items = data_retriever.make_stac_item_query(
        stac_collection_id=stac_collection_id, 
        location_filter=request.location_filter, 
        time_interval=request.time_interval, 
        limit=request.limit, 
    )
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
    
    filepath = data_retriever.create_notebook_export(
        stac_collection_id=stac_collection_id, 
        location_filter=request.location_filter, 
        time_interval=request.time_interval, 
    )
    
    if filepath is None:
        print(f"something went wrong.. could not create python notebook for STAC download...")
        return None

    return FileResponse(filepath, media_type="ipynb", background=BackgroundTask(cleanup, filepath))


@app.post("/geotweetRequest")
def get_all_geotweets(request: GeotweetRequest):
    
    geotweets = data_retriever.get_geotweets(
        only_floods=request.only_floods, 
        limit = request.limit, 
    )
    print(f"returning {len(geotweets)} geotweets...")
    return geotweets



########################################
# HELPER FUNCTIONS
def cleanup(filepath):
    # remove file after sending response to client
    os.remove(filepath)
