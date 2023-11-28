from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import yaml


# add path to import queries
import sys
sys.path.append("src/")

from queries.web_query import *
from queries.arango_query import *
from queries.QueryRequest import *
from queries.stac_queries import make_stac_item_query
from queries.QueryAnalyzer import QueryAnalyzer
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


# TODO: check if this is the correct way to do this
origins = [
    "http://localhost",
    frontend_url, 
    "http://localhost:8080", 
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



# create QueryAnalyzer class
qa = QueryAnalyzer(geonames_username=geonames_username)


# DEFINE ENDPOINTS

@app.post("/pubRequest")
def make_pub_request(request: PubRequest) -> tuple[str, list[dict]]:
    results = make_publications_query(
        db=db, 
        graph_name=graph_name, 
        query=request.query, 
        keywords=request.keywords, 
        #limit=request.limit, 
    )
    return ('publications', results)

@app.post("/stacCollectionRequest")
def make_stac_collection_request(request: STACCollectionRequest) -> tuple[str, list[dict]]:
    results = make_stac_collection_query(
        db=db, 
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
        db=db, 
        graph_name=graph_name, 
        stac_collection_id=stac_collection_id, 
        location_filters=request.location_filters, 
        time_interval=request.time_interval, 
        limit=request.limit)

    return ('stac_items', stac_items)

@app.get("/keywordRequest")
def get_all_keywords_request():
    keywords = get_all_keywords(db=db)
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


def home():
    return "Hello, World!"

