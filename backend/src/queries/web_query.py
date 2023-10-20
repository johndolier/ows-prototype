import requests
import json

from utils import normalize_scoring_range

endpoint = 'https://chatnoir.web.webis.de/api/v1/_search'


def make_web_query(api_key:str, query:str, limit:int = 100, verbose:bool = False) -> list[dict]:
    body = {
        'apikey': api_key, 
        'query': query, 
        'index': ['cw12'], # TODO use other indices as well?  
        'size': limit, 
        'pretty': True, 
    }
    response = requests.post(endpoint, json.dumps(body))
    
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

