from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import yaml
from pyArango.connection import Connection
from dotenv import load_dotenv, find_dotenv
import os


# NOTE: .env file is in ows_prototype/frontend folder! this relative path only works when script is launched from parent/backend directory!
success = load_dotenv('../frontend/.env')
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

#from queries.web_query import make_web_request
#from queries.arango_query import *
#from queries.stac_queries import make_stac_item_query
from queries.Requests import *
from queries.QueryAnalyzer import QueryAnalyzer
from queries.DataRetriever import DataRetriever



with open('src/config.yml', 'r') as file:
    config = yaml.safe_load(file)
    arango_config = config['arango']
    #arango_config = config['arango_dev']
    web_api_key = config['web_api_key']
    graph_name = arango_config.get('graph')

# CREATE BACKEND API 
app = FastAPI()

origins = [
    "http://localhost",
    f"http://localhost:{FRONTEND_PORT}",
    f"{APP_URL}:{FRONTEND_PORT}", 
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ESTABLISH ARANGODB CONNECTION
conn = Connection(
    username=arango_config.get('username'), 
    password=arango_config.get('password'), 
    arangoURL=ARANGO_URL
)
db = conn.databases[arango_config.get('database')]


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

@app.post("/stacItemRequest")
def make_stac_item_request(request: STACItemRequest) -> tuple[str, list[dict]]:
    # TODO adapt function for locationFilters
    # split collection id string to retrieve collection
    response = ('stac_collections', [])
    try:
        # omit first part of string (STACCollection/)
        stac_collection_id = request.collection_id.split('/')[1]
    except Exception as e:
        # invalid format!
        print(f"failed to process stac item request for request {request}")
        print(e)
        return response
    
    stac_items = data_retriever.make_stac_item_query(
        stac_collection_id=stac_collection_id, 
        location_filters=request.location_filters, 
        time_interval=request.time_interval, 
        limit=request.limit)

    return ('stac_items', stac_items)

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

