import requests
import json

from utils import normalize_scoring_range


#WEB_INDEX_SOURCE = "chatnoir"
WEB_INDEX_SOURCE = "prototype_webindex"


CHATNOIR_ENDPOINT = 'https://chatnoir.web.webis.de/api/v1/_search'
PROTOTYPE_WEBINDEX_ENDPOINT = 'https://qnode.eu/prosa/service/search/'


def make_web_request(request_dict:dict, verbose:bool=False):
    query = request_dict.get('query')
    api_key = request_dict.get('api_key')
    limit = request_dict.get('limit')
    if WEB_INDEX_SOURCE == "chatnoir":
        results = make_web_query_chatnoir(api_key=api_key, query=query, limit=limit, verbose=verbose)
    elif WEB_INDEX_SOURCE == "prototype_webindex":
        results = make_web_query_prototype_webindex(query=query, limit=limit, verbose=verbose)
    else:
        print(f"error - invalid state! did not find web index source for {WEB_INDEX_SOURCE}")
        results = None
    return results

def make_web_query_prototype_webindex(query:str, limit:int = 100, verbose:bool = False) -> list[dict]:
    request_url = f"{PROTOTYPE_WEBINDEX_ENDPOINT}?query={query}&index=demo-dlrsciencesearch&limit={limit}"
    if verbose:
        print(f"making request on url: {request_url}")
    response = requests.get(request_url)
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
    return results


def make_web_query_chatnoir(api_key:str, query:str, limit:int = 100, verbose:bool = False) -> list[dict]:
    body = {
        'apikey': api_key, 
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
    return results

