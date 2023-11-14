import requests
import json
import pystac_client
import geojson
import planetary_computer
from pyArango.connection import DBHandle
from sentence_transformers import SentenceTransformer


from utils import normalize_scoring_range
from queries.arango_queries import *


CHATNOIR_ENDPOINT = 'https://chatnoir.web.webis.de/api/v1/_search'
PROTOTYPE_WEBINDEX_ENDPOINT = 'https://qnode.eu/ows/prosa/service/'

PC_API = "https://planetarycomputer.microsoft.com/api/stac/v1"
TERRABYTE_API = "https://stac.terrabyte.lrz.de/public/api"
GEOSERVICE_API = "https://geoservice.dlr.de/eoc/ogc/stac/v1"



class DataRetriever:
    def __init__(self, web_api_key:str, db_instance:DBHandle, graph_name:str) -> None:
        self.api_key = web_api_key
        self.db = db_instance
        self.graph_name = graph_name

        # uncomment one of the following lines to use the preferred web index
        self.index_source = "chatnoir"
        #self.index_source = "prototype_webindex"


    def make_web_query(self, query:str, limit:int, verbose:bool=False):
        '''
            Makes web query on selected source (chatnoir or prototype webindex application -> OWS)
        '''
        if self.index_source == "chatnoir":
            results = self._make_web_query_chatnoir(query=query, limit=limit, verbose=verbose)
        elif self.index_source == "prototype_webindex":
            results = self._make_web_query_prototype_webindex(query=query, limit=limit, verbose=verbose)
        else:
            print(f"error - invalid state! did not find web index source for {self.index_source}")
            results = None
        return results
    
    def make_stac_item_query(self, stac_collection_id:str, location_filters:list[dict], time_interval:list, limit:int = 100) -> list[dict]:
        # TODO find better request strategy for STAC items? 
        query_params = {
            'doc_id': stac_collection_id, 
            'graph_name': self.graph_name, 
            }
        try:
            # get key from first (and only) element
            stac_source = self.db.AQLQuery(STAC_SOURCE_QUERY, bindVars=query_params, rawResults=True)[0].get('_key', None)
        except Exception as e:
            print(e)
            print(f"error - could not load stac collection node with id {stac_collection_id}")
            return None
        
        if stac_source == 'geoservice_collections':
            catalog_url = GEOSERVICE_API
        elif stac_source == 'planetary_computer_collections':
            catalog_url = PC_API
        elif stac_source == 'terrabyte_collections':
            catalog_url = TERRABYTE_API
        else:
            print(f"error - invalid state! did not find stac source for {stac_collection_id} ({stac_source})")
            return None
        catalog = self._get_catalog(catalog_url=catalog_url)

        items_list = []
        geojson_polygon = self._get_geojson_from_location_filters(location_filters)
        search_items = catalog.search(
            max_items = limit, 
            collections = stac_collection_id, 
            intersects = geojson_polygon, 
            datetime = time_interval, 
        )
        search_items = list(search_items.items())
        # found items in planetary computer
        for item in search_items:
            item_api_str = f"{catalog_url}/collections/{stac_collection_id}/items/{item.id}"
            #print(f"send get request to {item_api_str}")
            response = requests.get(item_api_str)
            item_dict = json.loads(response.text)
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

    def make_stac_collection_query(self, query:str, keywords:list[str], limit:int = 500) -> list[dict]:
        ''' 
            Makes query on arangodb to retrieve stac collections that match the query
        '''
        # TODO automatically get connected eo missions/instruments

        # for now, keyword list are used to retrieve stac collections
        keyword_query = ''
        for word in keywords:
            keyword_query += f"{word} "
        keyword_query = keyword_query.strip()

        model = SentenceTransformer('msmarco-distilbert-base-v4')
        keyword_query_emb = model.encode(keyword_query).tolist()
        query_params = {
            #'query': keyword_query, 
            'query_embedding': keyword_query_emb,  
            #'limit': limit, 
            'sim_threshold': 0.1, 
        }
        try:
            result = self.db.AQLQuery(SIMPLE_STAC_EMB_QUERY, bindVars=query_params, rawResults=True)
        except Exception as e:
            print(e)
            result = []
        result = [e for e in result]

        # convert iterable query to list of dicts
        transformed_results = []
        # normalize score
        # TODO find better way (temporary solution)
        min_score = float('inf')
        max_score = 0
        for doc in result:
            stac = doc.get('stac')
            if not stac:
                continue
            score = doc.get('score', 10)
            stac['score'] = score
            if score < min_score:
                min_score = score
            if score > max_score:
                max_score = score
            stac['eo_objects'] = doc.get('eo_objects', [])
            stac['loading'] = False # quick hack for frontend 
            stac['stac_items'] = [] # hack for frontend
            transformed_results.append(stac)

        #transformed_results = normalize_scoring_range(transformed_results, min_score, max_score)
        return transformed_results

    def get_all_keywords(self, batchSize:int = 1000):
        try:
            result = self.db.AQLQuery(ALL_KEWORDS_QUERY, batchSize=batchSize, rawResults=True)
            result = [key for key in result] # transform query object to list of keywords
        except Exception as e:
            print(e)
            result = []
        return result
    
    def make_publications_query(self, query:str, keywords:list[str] = None, limit:int = 500) -> list[dict]:
        '''
            Makes query on arangodb to retrieve publications that match the query
        '''
        # for now, keyword list are used to retrieve stac collections
        keyword_query = ''
        for word in keywords:
            keyword_query += f"{word} "
        keyword_query = keyword_query.strip()
        
        #model = SentenceTransformer('msmarco-distilbert-base-v4')
        #query_emb = model.encode(query).tolist()
        query_params = {
            'query': keyword_query,
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
        transformed_results = []
        min_score = float('inf')
        max_score = 0
        for doc in result:
            pub = doc.get('pub')
            if not pub:
                continue
            score = doc.get('score', 0)
            pub['score'] = score
            if score < min_score:
                min_score = score
            if score > max_score:
                max_score = score
            pub['eo_objects'] = doc.get('eo_objects', [])
            transformed_results.append(pub)

        transformed_results = normalize_scoring_range(transformed_results, min_score, max_score)
        return transformed_results


  # WEB QUERY HELPER FUNCTIONS
    def _make_web_query_chatnoir(self, query:str, limit:int = 100, verbose:bool = False) -> list[dict]:
        body = {
            'apikey': self.api_key, 
            'query': query, 
            'index': ['cw12'], # TODO use other indices as well?  
            'size': limit, 
            'pretty': True, 
        }
        response = requests.post(CHATNOIR_ENDPOINT, json.dumps(body))
    
        try:
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
                'title': title, 
                'url': url, 
                'text': text, 
                'is_html': True,
            })
        return transformed_results

    def _make_web_query_prototype_webindex(self, query:str, limit:int = 100, verbose:bool = False) -> list[dict]:
        request_url = f"{PROTOTYPE_WEBINDEX_ENDPOINT}search?q={query}&index=demo-dlrsciencesearch&limit={limit}"
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
                'title': title, 
                'url': url, 
                'text': text, 
                'is_html': False,
            })
        return transformed_results

  # STAC QUERY HELPER FUNCTIONS
    def _get_catalog(self, catalog_url:str):
        if "planetarycomputer" in catalog_url:
            catalog = pystac_client.Client.open(catalog_url, modifier=planetary_computer.sign_inplace)
        else:
            catalog = pystac_client.Client.open(catalog_url)
        return catalog

    def _get_geojson_from_location_filters(self, location_filters):
        ''' Transforms the location filter geoBounds into a geojson object for querying stac catalogs '''
        # TODO generalize for more cases
        # for now, only bounding boxes are supported!
        if len(location_filters) == 1:
            # only one filter provided
            bbox = location_filters[0]['coords']
            coordinates = [[
                [bbox[1], bbox[0]], 
                [bbox[3], bbox[0]], 
                [bbox[3], bbox[2]], 
                [bbox[1], bbox[2]], 
                [bbox[1], bbox[0]]
            ]]
            return geojson.Polygon(coordinates)

        # multiple filters
        coordinates = []
        for filter in location_filters:
            bbox = filter['coords']
            new_coord = [[
                [bbox[1], bbox[0]], 
                [bbox[3], bbox[0]], 
                [bbox[3], bbox[2]], 
                [bbox[1], bbox[2]], 
                [bbox[1], bbox[0]]
            ]]
            coordinates.append(new_coord)
      
        return geojson.MultiPolygon(coordinates)


  # ARANGODB QUERY HELPER FUNCTIONS

    def _get_nodes_from_keyword(self, keyword:str) -> list[str]:
        # returns list of id's wich are connected with HasKeyword edge (either STACCollection or Publication)
        keyword = self._create_key_from_keyword(keyword=keyword.lower())
        query_params = {
            'keyword': f'Keyword/{keyword}', 
        }
        try:
            result = self.db.AQLQuery(NODE_FROM_KEYWORD_QUERY, bindVars=query_params, rawResults=True)
        except Exception as e:
            print(e)
            result = []
        return result

    def _get_related_eo_connections(self, key:str, collection:str) -> list[str]:
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

    def _create_key_from_keyword(self, keyword:str) -> str:
        # keyword argument should already be lowercase!
        import re
        try:
            new_key = re.sub('[^A-Za-z0-9]+', '', keyword).strip()
            return new_key
        except:
            return None
    



