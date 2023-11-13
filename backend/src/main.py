from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import yaml
from pyArango.connection import Connection
from dotenv import load_dotenv, find_dotenv
import os

# NOTE: .env file is in ows_prototype/frontend folder! this relative path only works when script is launched from parent/backend directory!
load_dotenv('../frontend/.env')
BACKEND_PORT = os.environ.get("VUE_APP_BACKEND_PORT")
FRONTEND_PORT = os.environ.get("VUE_APP_FRONTEND_PORT")
APP_URL = os.environ.get("VUE_APP_URL")
ARANGO_PORT = os.environ.get("ARANGO_PORT")
ARANGO_URL = os.environ.get("ARANGO_URL")

if BACKEND_PORT is None:
    print("warning - could not load BACKEND_PORT env var!")
if FRONTEND_PORT is None:
    print("warning - could not load FRONTEND_PORT env var!")
if APP_URL is None:
    print("warning - could not load APP_URL env var!")
if ARANGO_PORT is None or ARANGO_URL is None:
    print("warning - could not load ARANGO_PORT/ARANGO_URL env var!")

# extend ARANGO_URL with port number
ARANGO_URL = f"{ARANGO_URL}:{ARANGO_PORT}"


# add path to import queries
import sys
sys.path.append("src/")

from queries.web_query import *
from queries.arango_query import *
from queries.QueryRequest import *
from queries.stac_queries import make_stac_item_query, fetch_stac_source_information, create_stac_export_notebook
from queries.QueryAnalyzer import QueryAnalyzer


with open('src/config.yml', 'r') as file:
    config = yaml.safe_load(file)
    arango_config = config['arango']
    #arango_config = config['arango_dev']
    web_api_key = config['web_api_key']
    graph_name = arango_config.get('graph')

# CREATE BACKEND API 
app = FastAPI()

ORIGINS = [
    "http://localhost",
    f"http://localhost:{FRONTEND_PORT}",
    f"{APP_URL}:{FRONTEND_PORT}", 
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ESTABLISH ARANGODB CONNECTION
CONN = Connection(
    username=arango_config.get('username'), 
    password=arango_config.get('password'), 
    arangoURL=ARANGO_URL
)
DB = CONN.databases[arango_config.get('database')]

# fetch information for stac sources
STAC_SOURCE_DICT = fetch_stac_source_information(db=DB)

# create QueryAnalyzer class
QA = QueryAnalyzer(geonames_username='johndolier')


# DEFINE ENDPOINTS

@app.post("/pubRequest")
def make_pub_request(request: PubRequest) -> tuple[str, list[dict]]:
    results = make_publications_query(
        db=DB, 
        graph_name=graph_name, 
        query=request.query, 
        keywords=request.keywords, 
        #limit=request.limit, 
    )
    return ('publications', results)

@app.post("/stacCollectionRequest")
def make_stac_collection_request(request: STACCollectionRequest) -> tuple[str, list[dict]]:
    results = make_stac_collection_query(
        db=DB, 
        graph_name=graph_name, 
        query=request.query, 
        keywords=request.keywords, 
        #limit=request.limit, 
    )
    
    return ('stac_collections', results)

@app.post("/webRequest")
def make_web_request(request: WebRequest) -> tuple[str, list[dict]]:
    results = make_web_query(
        api_key=web_api_key, 
        query=request.query, 
        #limit=request.limit, 
        verbose=True,
    )
    return ('web_documents', results)

@app.post("/stacItemRequest")
def make_stac_item_request(request: STACItemRequest) -> tuple[str, list[dict]]:
    # TODO adapt function for locationFilters
    # split collection id string to retrieve collection
    response = ('stac_collections', [])
    try:
        stac_collection_id = request.collection_id.split('/')[1]
    except Exception as e:
        # invalid format!
        print(f"failed to process stac item request for request {request}")
        print(e)
        return response
    
    stac_items = make_stac_item_query(
        db=DB, 
        graph_name=graph_name, 
        stac_collection_id=stac_collection_id, 
        location_filters=request.location_filters, 
        time_interval=request.time_interval, 
        limit=request.limit, 
        stac_source_dict=STAC_SOURCE_DICT, 
    )

    return ('stac_items', stac_items)

@app.get("/keywordRequest")
def get_all_keywords_request():
    keywords = get_all_keywords(db=DB)
    return keywords

@app.post("/queryAnalyzerRequest")
def analyze_user_query(request: QueryAnalyzerRequest) -> dict:
    ''' Takes the user query and extracts possible locations, time mentions and general keywords '''
    analyzer_result = QA.analyze_query(user_query=request.query)
    #print(f"locations: {analyzer_result.get('locations')}")
    #print(f"dates: {analyzer_result.get('dates')}")
    #print(f"general keywords: {analyzer_result.get('general_keywords')}")
    return analyzer_result

@app.post("/geoparseRequest")
def get_location_from_user_query(request: GeoparseRequest) -> tuple[str, list]:
    ''' Extract locations and bboxes from user query if present '''
    geocoding_result = QA.get_location_and_geobounds_list(request.query)
    # TODO transform data for client? 

    return ('locations', geocoding_result)

@app.post("/notebookExportRequest")
def create_notebook_export(request: NotebookExportRequest):
    ''' Creates a jupyter notebook for export from the parameters of the request '''
    
    pass

from datetime import datetime

create_stac_export_notebook(
    db=DB, 
    graph_name=graph_name, 
    stac_collection_id="gnatsgo-tables", 
    location_filters={
        'type': 'polygon', 
        'coordiantes': [1, [2,3], [4], 5]
    },
    time_interval=datetime.now(), 
    limit=10, 
    stac_source_dict=STAC_SOURCE_DICT
    )
