import requests
import json
import pystac_client
import geojson
import planetary_computer
from pyArango.connection import DBHandle
from sentence_transformers import SentenceTransformer
import nbformat as nbf
import uuid


from utils import normalize_scoring_range
from queries.arango_queries import *


CHATNOIR_ENDPOINT = 'https://chatnoir.web.webis.de/api/v1/_search'
PROTOTYPE_WEBINDEX_ENDPOINT = 'https://qnode.eu/ows/prosa/service/'
MOSAIC_ENDPOINT = 'https://qnode.eu/ows/mosaic/service/'

DEMO_INDEX_MOSAIC = "dlrprototype"
DEMO_INDEX_STANDARD = "demo-dlrsciencesearch"

PC_API = "https://planetarycomputer.microsoft.com/api/stac/v1"
TERRABYTE_API = "https://stac.terrabyte.lrz.de/public/api"
GEOSERVICE_API = "https://geoservice.dlr.de/eoc/ogc/stac/v1"



class DataRetriever:
    def __init__(self, web_api_key:str, db_instance:DBHandle, graph_name:str, web_api:int) -> None:
        self.api_key = web_api_key
        self.db = db_instance
        self.graph_name = graph_name
        
        if web_api == 1:
            # chatnoir
            print("DataRetriever - using chatnoir web index")
            self.index_source = "chatnoir"
        elif web_api == 2:
            # prototype webindex
            print("DataRetriever - using prototype web index")
            self.index_source = "prototype_webindex"
        elif web_api == 3:
            print("DataRetriever - using Mosaic open web index")
            self.index_source = "mosaic"
        else:
            # default
            print("Error - invalid web api source!")
            print("Using chatnoir web index")
            self.index_source = "chatnoir"
        
        # fetch STAC source information
        self.stac_source_dict = self.__fetch_stac_source_information()


    def make_web_query(self, query:str, limit:int, location_filter:dict, verbose:bool=False):
        '''
            Makes web query on selected source (chatnoir or prototype webindex application -> OWS)
            Mosaic request also takes location filter
        '''
        if self.index_source == "chatnoir":
            results = self.__make_web_query_chatnoir(query=query, limit=limit, verbose=verbose)
        elif self.index_source == "prototype_webindex":
            results = self.__make_web_query_prototype_webindex(query=query, limit=limit, verbose=verbose)
        elif self.index_source == "mosaic":
            results = self.__make_web_query_mosaic_webindex(query=query, limit=limit, location_filter=location_filter, verbose=verbose)
        else:
            print(f"error - invalid state! did not find web index source for {self.index_source}")
            results = None
        return results
    
    def make_stac_item_query(self, stac_collection_id:str, location_filter:list[dict], time_interval:list, limit:int = 100) -> list[dict]:
        # TODO find better request strategy for STAC items? 
        stac_source = self.__get_stac_source(stac_collection_id=stac_collection_id)
        api_link = self.stac_source_dict[stac_source]['api_link']
        catalog = self.__get_catalog(api_link)
        
        location_filter = self.__get_geojson_from_location_filters(location_filter)
        time_interval = self.__get_time_interval(time_interval)
        
        search = catalog.search(
            max_items = limit, 
            collections = stac_collection_id, 
            intersects = location_filter, 
            datetime = time_interval, 
        )
        
        # found items in planetary computer
        items_list = []
        for item in search.items():
            item_dict = item.to_dict()
            try:
                # catalogs have different paths to access preview img -> temporary solution: hardcoded paths
                if stac_source == 'planetary_computer_collections':
                    item_dict['img_link'] = item_dict.get('assets', {}).get('rendered_preview', {}).get('href')
                elif stac_source == 'geoservice_collections':
                    item_dict['img_link'] = item_dict.get('assets', {}).get('thumbnail', {}).get('href')
                else:
                    # image not available for terrabyte stac items
                    item_dict['img_link'] = None            
            except Exception as e:
                print(e)
                print("failed to load rendered preview (planetary computer)")
                item_dict['img_link'] = None
            items_list.append(item_dict)
        return items_list

    def create_notebook_export(self, stac_collection_id:str, location_filter:list[dict], time_interval:list) -> str:
        ''' 
            This function parses the arguments and generates a Python notebook from a template file ('assets/STAC_notebook_template.ipynb')
            Placeholders get replaced by the specified arguments (STAC collection ID, location coordinates, time interval...)
        '''
        
        stac_source = self.__get_stac_source(stac_collection_id=stac_collection_id)
        api_link = self.stac_source_dict[stac_source]['api_link']
        
        # transform location filters (coordinates) and time interval
        coordinates = self.__get_geojson_from_location_filters(location_filter).get('coordinates') # can be None
        time_interval = self.__get_time_interval(time_interval)        
            
        template_notebook = nbf.read('assets/STAC_notebook_template.ipynb', as_version=4)
        
        PARSE_BLOCK_IDX = 5 # this is the code block that has to be filled in with custom values
        
        argument_source_code = template_notebook['cells'][PARSE_BLOCK_IDX]['source']
        
        # modify source code
        argument_source_code = argument_source_code.replace('<<api_link>>', str(api_link))
        argument_source_code = argument_source_code.replace('<<coordinates>>', str(coordinates))
        argument_source_code = argument_source_code.replace('<<stac_collection_id>>', str(stac_collection_id))
        
        template_notebook['cells'][PARSE_BLOCK_IDX]['source'] = argument_source_code
        
        time_argument_source_code = template_notebook['cells'][PARSE_BLOCK_IDX+1]['source']
        if time_interval is None:
            time_argument_source_code += "\n#No time range arguments provided\ntime_range=None"
        else:
            time_argument_source_code += self.__get_time_interval_source_code(time_interval)
        template_notebook['cells'][PARSE_BLOCK_IDX+1]['source'] = time_argument_source_code
        
        filepath = 'assets/custom_notebook.ipynb'
        nbf.write(template_notebook, filepath)
        return filepath
        
    def make_stac_collection_query(self, query:str, keywords:list[str], location_filter:dict, limit:int = 500) -> list[dict]:
        ''' 
            Makes query on arangodb to retrieve stac collections that match the query
        '''
        # TODO automatically get connected eo missions/instruments

        # alternatively, we can use the keywords to form a query (location and time is evicted from this query)
        query = ''
        for word in keywords:
            query += f"{word} "
        query = query.strip()
        

        model = SentenceTransformer('msmarco-distilbert-base-v4')
        query_embedding = model.encode(query).tolist()
        query_params = {
            #'query': keyword_query, 
            'query_embedding': query_embedding,  
            #'limit': limit, 
            'sim_threshold': 0.1, 
        }
        try:
            result = self.db.AQLQuery(SIMPLE_STAC_EMB_QUERY, bindVars=query_params, rawResults=True)
        except Exception as e:
            print(e)
            result = []
        result = [e for e in result]
        
        # parse location filter
        bbox = self.__get_bbox_from_location_filters(location_filter=location_filter)
        # filter STAC collections by location filter
        if bbox:
            result = self.__filter_stac_collections_by_location(result, bbox)
        else:
            # no location filter passed -> no spatial filtering applied
            pass

        # add attributes to stac dictionary (score, eo_objects, loading (flag), stac_items (empty list))
        transformed_results = self.__transform_raw_stac_collection_results(result)
        return transformed_results

    def get_all_keywords(self, batchSize:int = 1000):
        try:
            result = self.db.AQLQuery(ALL_KEYWORDS_QUERY, batchSize=batchSize, rawResults=True)
            keyword_list = []
            for node in result:
                keyword_list.append({
                    'id': node['_id'], 
                    'name': node['keyword_full']
                })
        except Exception as e:
            print(e)
            keyword_list = []
        return keyword_list
    
    def get_all_authors(self, batchSize:int = 1000):
        try:
            result = self.db.AQLQuery(ALL_AUTHORS_QUERY, batchSize=batchSize, rawResults=True)
            author_list = []
            for node in result:
                first_name = node['first_name']
                last_name = node['last_name']
                name = f"{first_name} {last_name}"
                author_list.append({
                    'id': node['_id'], 
                    'first_name': first_name, 
                    'last_name': last_name, 
                    'name': name
                })
        except Exception as e:
            print(e)
            author_list = []
        return author_list
    
    def get_all_eo_nodes(self, batchSize:int = 1000):
        try:
            result = self.db.AQLQuery(ALL_EO_NODES_QUERY, batchSize=batchSize, rawResults=True)
            eo_nodes_list = []
            for node in result:
                eo_nodes_list.append({
                    'id': node['id'], 
                    'name': node['name']
                })
        except Exception as e:
            print(e)
            eo_nodes_list = []
        return eo_nodes_list
    
    
    def make_publications_query(self, query:str, keywords:list[str] = None, limit:int = 500) -> list[dict]:
        '''
            Makes query on arangodb to retrieve publications that match the query
        '''
        # alternatively, we can use the keywords to form a query (location and time is evicted from this query)
        # query = ''
        # for word in keywords:
        #     query += f"{word} "
        # query = query.strip()
        
        #model = SentenceTransformer('msmarco-distilbert-base-v4')
        #query_emb = model.encode(query).tolist()
        query_params = {
            'query': query,
            #'query_embedding': query_emb,  
            'sim_score': 0.9, 
        }
        try:
            result = self.db.AQLQuery(SIMPLE_PUB_ARANGOSEARCH_QUERY, bindVars=query_params, rawResults=True)
        except Exception as e:
            print(e)
            result = []
        # convert iterable query to list of dicts
        # transform dictionary
        transformed_results = self.__transform_raw_publication_results(result)
        return transformed_results

    def get_geotweets(self, only_floods:bool=False, limit:int = 100) -> list[dict]:
        '''
            Return list of geotweets
        '''
        path = "src/database/geotweets/geotweets_sample.geojson"
        
        with open(path, "r") as file:
            # read geojson file
            geojson_data = json.load(file)

        tweets = geojson_data.get('features', [])
        if not only_floods:
            return tweets[:limit]
        
        # filter geotweets
        filtered_tweets = []
        for tweet in tweets:
            try:
                if not tweet['properties']['contains_flood']:
                    continue
                filtered_tweets.append(tweet)
            except Exception as e:
                print(e)
                continue
        
        return filtered_tweets[:limit]
    
    def make_graph_query(self, keywords_list, authors_list, eo_list):
        ''' Makes graph query for publications and stac collections that are connected to the given keywords, EO Missions/instruments and authors (in case with publications)
            additionally makes normal web query with keyword list to get web documents (currently disabled)
        '''
        
        authors = [element['id'] for element in authors_list]
        keywords = [element['id'] for element in keywords_list]
        eo_nodes = [element['id'] for element in eo_list]
        
        stac_query_params = {
            'keyword_list': keywords, 
            'eo_list': eo_nodes, 
        }
        try:
            results = self.db.AQLQuery(GRAPH_KEYWORD_STAC_QUERY, bindVars=stac_query_params, rawResults=True)
            results = [e for e in results]
            stac_collections = self.__transform_raw_stac_collection_results(results)
        except Exception as e:
            print(e)
            stac_collections = []
        
        pub_query_params = {
            'author_list': authors, 
            'keyword_list': keywords, 
            'eo_list': eo_nodes, 
        }
        try:
            results = self.db.AQLQuery(GRAPH_KEYWORD_PUB_QUERY, bindVars=pub_query_params, rawResults=True)
            publications = self.__transform_raw_publication_results(results)
        except Exception as e:
            print(e)
            publications = []
        
        # web_results = self.make_web_query(query=' '.join(keywords), limit=100)
        # return {'stac_collections': stac_collections, 'publications': publications, 'web_documents': web_results}
        return {'stac_collections': stac_collections, 'publications': publications}      
        
        
  # WEB QUERY HELPER FUNCTIONS
    def __make_web_query_chatnoir(self, query:str, limit:int = 100, verbose:bool = False) -> list[dict]:
        body = {
            'apikey': self.api_key, 
            'query': query, 
            'index': ['cw12'], # TODO use other indices as well?  
            'size': limit, 
            'pretty': True, 
        }
        response = requests.post(CHATNOIR_ENDPOINT, json.dumps(body))
        try:
            if response.status_code > 500 and response.status_code < 600:
                # SERVER ERROR
                print(f"Server error (Chatnoir) - status code {response.status_code}")
                response_dict = {}
            else:
                response_dict = json.loads(response.text)
        except Exception as e:
            print(f"Exception in parsing response - {e}")
            print(f"Status code: {response.status_code}")
            response_dict = {}

        meta = response_dict.get('meta', {})
        results = response_dict.get('results', [])

        if verbose and meta:
            print(f"query time: {meta.get('query_time')}, total results: {meta.get('total_results')}")
        
        # normalize score
        # TODO find better (safer) way
        if results:
            min_score = min([result['score'] for result in results])
            max_score = max([result['score'] for result in results])
            results = normalize_scoring_range(results, min_score, max_score)

        # transform results to fit standardized interface
        transformed_results = []
        for result in results:
            title = result.get('title', '')
            url = result.get('target_uri', '')
            text = result.get('snippet', '')
            transformed_results.append({
                'id': uuid.uuid4(), 
                'title': title, 
                'url': url, 
                'text': text, 
                'is_html': True,
                'locations': [], 
            })
        return transformed_results

    def __make_web_query_prototype_webindex(self, query:str, limit:int = 100, verbose:bool = False) -> list[dict]:
        request_url = f"{PROTOTYPE_WEBINDEX_ENDPOINT}search?q={query}&index={DEMO_INDEX_STANDARD}&limit={limit}"
        if verbose:
            print(f"making request on url: {request_url}")
        
        response = requests.get(request_url)
        try:
            response_dict = json.loads(response.text)
        except Exception as e:
            print(f"Exception in parsing response - {e}")
            print(f"Status code: {response.status_code}")
            response_dict = {}

        results = response_dict.get('results', [])
        
        # transform results to fit standardized interface
        transformed_results = []
        for result in results:
            title = result.get('title', '')
            url = result.get('url', '')
            text = result.get('textSnippet', '')
            transformed_results.append({
                'id': uuid.uuid4(), 
                'title': title, 
                'url': url, 
                'text': text, 
                'is_html': False,
                'locations': [], 
            })
        return transformed_results

    def __make_web_query_mosaic_webindex(self, query:str, limit:int = 1000, location_filter:dict={}, verbose:bool = False) -> list[dict]:
        bbox = self.__get_bbox_from_location_filters(location_filter=location_filter)
        if bbox:
            # bbox is S,W,N,E
            request_url = f"{MOSAIC_ENDPOINT}search?q={query}&index={DEMO_INDEX_MOSAIC}&limit={limit}&east={bbox[3]}&west={bbox[1]}&north={bbox[2]}&south={bbox[0]}"
        else:
            request_url = f"{MOSAIC_ENDPOINT}search?q={query}&index={DEMO_INDEX_MOSAIC}&limit={limit}"
        if verbose:
            print(f"making request on url: {request_url}")
        response = requests.get(request_url)
        try:
            response_dict = json.loads(response.text)
        except Exception as e:
            print(f"Exception in parsing response - {e}")
            print(f"Status code: {response.status_code}")
            response_dict = {}

        results = response_dict.get('results', [])
        if not results:
            return []

        results = results[0]['dlrprototype']
        
        # transform results to fit standardized interface
        transformed_results = []
        for result in results:
            title = result.get('title', '')
            url = result.get('url', '')
            text = result.get('textSnippet', '')
            locations = result.get('locations', [])
            locations = self.__transform_locations_from_web_query(locations)
            transformed_results.append({
                'id': uuid.uuid4(), 
                'title': title, 
                'url': url, 
                'text': text, 
                'is_html': False,
                'locations': locations, 
            })
        return transformed_results
    
    def __transform_locations_from_web_query(self, raw_locations_list):
        locations = []
        # for now, only the first location is parsed, rest is discarded
        for location in raw_locations_list:
            loc_name = location.get('locationName')
            loc_entries = location.get('locationEntries', [])
            points = []
            if len(loc_entries) > 1:
                print(loc_entries)
            for entry in loc_entries:
                lat = entry['latitude']
                long = entry['longitude']
                # TODO fetch other info (e.g. country code)
                points.append((long, lat))
            multipoint_geojson = geojson.MultiPoint(points)
            location = {
                'name': loc_name, 
                'geojson': multipoint_geojson
            }
            locations.append(location)
            break
        return locations

# STAC QUERY HELPER FUNCTIONS
    def __get_catalog(self, catalog_url:str):
        if "planetarycomputer" in catalog_url:
            catalog = pystac_client.Client.open(catalog_url, modifier=planetary_computer.sign_inplace)
        else:
            catalog = pystac_client.Client.open(catalog_url)
        return catalog

    def __get_bbox_from_location_filters(self, location_filter:dict):
        if not isinstance(location_filter, dict) or not location_filter:
            # location filter is empty or not a dictionary!
            return None
        
        if location_filter['type'] == 'bbox':
            return location_filter['coords']
        else:
            # TODO handle different shapes
            return None
        
    def __filter_stac_collections_by_location(self, stac_collection_list, location_filter):
        print(location_filter)
        filtered_list = []
        for stac_collection in stac_collection_list:
            stac_collection_bbox_list = stac_collection.get('stac', {}).get('extent', {}).get('spatial', {}).get('bbox', {})
            if not stac_collection_bbox_list:
                print(f"error - did not find spatial extent for stac collection! {stac_collection.get('stac', {}).get('_id')}")
            
            # id = stac_collection.get('stac', {}).get('_id')
            for bbox in stac_collection_bbox_list:
                if self.__bbox_overlaps(bbox, location_filter):
                    filtered_list.append(stac_collection)
                    break

        return filtered_list
            
    def __bbox_overlaps(self, spatial_extent_bbox, location_filter_bbox):
        ''' Returns true if at least one point of bbox1 is inside bbox2 (intersection OR containment) 
        '''
        
        # spatial extent bbox has format: long/lat long/lat; (W,S,E,N)
        # location filter bbox has format: lat/long lat/long; (S,W,N,E)
        bbox1 = [spatial_extent_bbox[1], spatial_extent_bbox[0], spatial_extent_bbox[3], spatial_extent_bbox[2]]
        bbox2 = [location_filter_bbox[0], location_filter_bbox[1], location_filter_bbox[2], location_filter_bbox[3]]
        
        if (bbox1[3] < bbox2[1] or bbox1[1] > bbox2[3] or bbox1[2] < bbox2[0] or bbox1[0] > bbox2[2]):
            # no intersection
            return False
        
        # bbox1 and bbox2 intersect in some way 
        return True
    
    
    def __get_geojson_from_location_filters(self, location_filter:dict):
        ''' Transforms the location filter geoBounds into a geojson object for querying stac catalogs '''
        # TODO handle multiple different shapes
        if not isinstance(location_filter, dict) or not location_filter:
            # location filter is empty or not a dictionary!
            return {}
        
        coordinates = []
        if location_filter['type'] == 'bbox':
            bbox = location_filter['coords']
            new_coord = [
                [bbox[1], bbox[0]], 
                [bbox[3], bbox[0]], 
                [bbox[3], bbox[2]], 
                [bbox[1], bbox[2]], 
                [bbox[1], bbox[0]]
            ]
        elif location_filter['type'] == 'polygon':
            new_coord = []
            for latlng_dict in location_filter['coords'][0]:
                lat = latlng_dict.get('lat')
                lng = latlng_dict.get('lng')
                new_coord.append([lng, lat])
                
            # add first point to list to close the loop
            last_lat = location_filter['coords'][0][0].get('lat')
            last_lng = location_filter['coords'][0][0].get('lng')
            new_coord.append([last_lng, last_lat])
        else:
            print(f"ERROR - unknown type {location_filter['type']}")
            return None
        
        coordinates.append(new_coord)
        return geojson.Polygon(coordinates)

    def __get_time_interval(self, time_interval:list):
        STR_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"
        if time_interval is None:
            return None
        if not isinstance(time_interval, list):
            return None
        if len(time_interval) != 2:
            return None
        if None in time_interval:
            # at least one value is None
            return None
        return time_interval

    def __fetch_stac_source_information(self):
        ''' Loop over STACSource nodes and save information in dictionary '''
        d = {}
        for node in self.db["STACSource"].fetchAll():
            d[node['_key']] = {
                'name': node['name'], 
                'api_link': node['api_link'], 
                'href': node['href']
            }
        return d

    def __get_stac_source(self, stac_collection_id:str):
        ''' 
            Performs an ArangoQuery to determine the source of the STAC collection
            Returns a string which identifies the source
        '''
        query_params = {
            'doc_id': stac_collection_id, 
            'graph_name': self.graph_name, 
        }
        try:
            # get key from first (and only) element
            response = self.db.AQLQuery(STAC_SOURCE_QUERY, bindVars=query_params, rawResults=True)
            #print(response)
            return response[0].get('_key', None)
        except Exception as e:
            print(e)
            print(f"error - could not load stac collection node with id {stac_collection_id}")
            return None
    
    def __get_time_interval_source_code(self, time_interval:list) -> str:
        return f"""
date_format = '%Y-%m-%dT%H:%M:%S.%fZ'
time_start_str='{str(time_interval[0])}'
time_end_str='{str(time_interval[1])}'

time_start = datetime.strptime(time_start_str, date_format)
time_end = datetime.strptime(time_end_str, date_format)

# the actual timerange (datetime objects)
time_range = [time_start, time_end]

"""

    def __transform_raw_stac_collection_results(self, results):
        transformed_results = []
        for doc in results:
            stac = doc.get('stac')
            if not stac:
                continue
            stac['score'] = doc.get('score', 10)
            stac['keywords'] = doc.get('keywords', [])
            stac_source = doc.get('stac_source', [])
            if len(stac_source) == 1:
                stac_source = stac_source[0]
            else:
                stac_source = {}
            stac['stac_source'] = stac_source
            eo_objects = doc.get('eo_objects', [])
            eo_missions, eo_instruments = self.__get_transformed_eo_objects(eo_objects)
            stac['eo_missions'] = eo_missions
            stac['eo_instruments'] = eo_instruments
            stac['loading'] = False # hack for frontend 
            stac['stac_items'] = [] # hack for frontend
            transformed_results.append(stac)
        return transformed_results
    
  # PUBLICATION QUERY HELPER FUNCTIONS
    def __transform_raw_publication_results(self, results):
        transformed_results = []
        for doc in results:
            pub = doc.get('pub')
            if not pub:
                continue
            pub['score'] = doc.get('score', 0)
            pub['authors'] = doc.get('authors', [])
            pub['keywords'] = doc.get('keywords', [])
            eo_objects = doc.get('eo_objects', [])
            eo_missions, eo_instruments = self.__get_transformed_eo_objects(eo_objects)
            pub['eo_missions'] = eo_missions
            pub['eo_instruments'] = eo_instruments

            transformed_results.append(pub)
        return transformed_results
    

  # ARANGODB QUERY HELPER FUNCTIONS

    def __get_nodes_from_keyword(self, keyword:str) -> list[str]:
        # returns list of id's wich are connected with HasKeyword edge (either STACCollection or Publication)
        keyword = self.__create_key_from_keyword(keyword=keyword.lower())
        query_params = {
            'keyword': f'Keyword/{keyword}', 
        }
        try:
            result = self.db.AQLQuery(NODE_FROM_KEYWORD_QUERY, bindVars=query_params, rawResults=True)
        except Exception as e:
            print(e)
            result = []
        return result

    def __get_related_eo_connections(self, key:str, collection:str) -> list[str]:
        # returns list of id's of eo missions/instruments that are connected to given node (either STACCollection or publication)
        node_id = f"{collection}/{key}"
        query_params = {
            'node_id': node_id, 
        }
        try:
            result = self.db.AQLQuery(EO_OBJECTS_FROM_NODE_QUERY, bindVars=query_params, rawResults=True)
        except Exception as e:
            print(e)
            result = []
        return result

    def __create_key_from_keyword(self, keyword:str) -> str:
        # keyword argument should already be lowercase!
        import re
        try:
            new_key = re.sub('[^A-Za-z0-9]+', '', keyword).strip()
            return new_key
        except:
            return None
    
    def __get_transformed_eo_objects(self, eo_objects:list) -> list[dict]:
        '''
            Transform EO objects to fit standardized interface
            Returns a list of EO Missions and EO Instruments
        '''
        eo_missions = []
        eo_instruments = []
        for eo_object_dict in eo_objects:
            eo_object = eo_object_dict.get('node', {})
            if not eo_object: continue
            eo_type = eo_object.get('_id').split('/')[0]
            if eo_type == 'EOMission':
                eo_missions.append({
                    'id': eo_object.get('_id'),
                    'full_name':  eo_object.get('mission_name_full'), 
                    'short_name': eo_object.get('mission_name_short'), 
                    'description': eo_object.get('description'),
                    'data_access_portal': eo_object.get('data_access_portal'), 
                    'agencies': eo_object.get('mission_agencies'), 
                    'mission_site': eo_object.get('mission_site'), 
                })
            elif eo_type == 'EOInstrument':
                eo_instruments.append({
                    'id': eo_object.get('_id'),
                    'full_name': eo_object.get('instrument_name_full'), 
                    'short_name': eo_object.get('instrument_name_short'), 
                    'description': eo_object.get('description'), 
                    'agencies': eo_object.get('instrument_agencies'), 
                    'instrument_status': eo_object.get('instrument_status'), 
                    'instrument_type': eo_object.get('instrument_type'), 
                    'instrument_technology': eo_object.get('instrument_technology'), 
                    'waveband_categories': eo_object.get('waveband_categories'), 
                })
            else:
                print(f"ERROR - unknown eo type {eo_type}")
                continue
            
        return eo_missions, eo_instruments


