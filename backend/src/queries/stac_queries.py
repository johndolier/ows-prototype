
import pystac_client
import planetary_computer
import geojson
import json
import requests
import nbformat as nbf


STAC_SOURCE_QUERY = """
FOR stac_coll in STACCollection
    FILTER stac_coll._key == @doc_id
    FOR v in 1..1 INBOUND stac_coll GRAPH @graph_name
        FILTER v._id LIKE "STACSource/%"
        return v
"""


def fetch_stac_source_information(db):
    ''' Loop over STACSource nodes and save information in dictionary '''
    d = {}
    for node in db["STACSource"].fetchAll():
        d[node['_key']] = {
            'name': node['name'], 
            'api_link': node['api_link'], 
            'href': node['href']
        }
    return d


def get_catalog(api_link:str, stac_source:str):
    if stac_source == 'planetary_computer_collections':
        # special case -> set modifier
        return pystac_client.Client.open(
            api_link, 
            modifier=planetary_computer.sign_inplace
        )
    
    return pystac_client.Client.open(
        api_link
    )

def get_stac_source(stac_collection_id:str, graph_name:str, db) -> str:
    ''' 
        Performs an ArangoQuery to determine the source of the STAC collection
        Returns a string which identifies the source
    '''
    query_params = {
        'doc_id': stac_collection_id, 
        'graph_name': graph_name, 
    }
    try:
        # get key from first (and only) element
        response = db.AQLQuery(STAC_SOURCE_QUERY, bindVars=query_params, rawResults=True)
        #print(response)
        return response[0].get('_key', None)
    except Exception as e:
        print(e)
        print(f"error - could not load stac collection node with id {stac_collection_id}")
        return None
    


def get_geojson_from_location_filters(location_filters):
    ''' Transforms the location filter geoBounds into a geojson object for querying stac catalogs '''
    if location_filters is None:
        # no location filters provided
        return None
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

def get_time_interval(time_interval:list, to_string:bool=False):
    STR_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"
    print(time_interval)
    if time_interval is None:
        return None
    if not isinstance(time_interval, list):
        return None
    if len(time_interval) != 2:
        return None
    if None in time_interval:
        # at least one value is None
        return None
    if to_string:
        # convert datetime arguments to string
        #time_start_str = time_interval[0].strftime(STR_FORMAT)
        #time_end_str = time_interval[1].strftime(STR_FORMAT)
        #time_interval = [time_start_str, time_end_str]
        pass
    return time_interval


def make_stac_item_query(db, graph_name:str, stac_collection_id:str, location_filters, time_interval, limit, stac_source_dict):
    '''
        Retrieve STAC items for the given stac collection, location, time and further parameters
    '''

    stac_source = get_stac_source(stac_collection_id=stac_collection_id, graph_name=graph_name, db=db)
    api_link = stac_source_dict[stac_source]['api_link']
    #print(api_link, stac_source)
    catalog = get_catalog(api_link, stac_source)
    location_filters = get_geojson_from_location_filters(location_filters)
    time_interval = get_time_interval(time_interval, to_string=False)
    print("before search....")
    print(location_filters)
    print(time_interval)
    search_items = catalog.search(
        max_items = limit, 
        collections = stac_collection_id, 
        intersects = location_filters, 
        datetime = time_interval, 
    )
    search_items = list(search_items.items())
    items_list = []
    # found items in planetary computer
    for item in search_items:
        item_api_str = f"{api_link}/collections/{stac_collection_id}/items/{item.id}"
        #print(f"send get request to {item_api_str}")
        response = requests.get(item_api_str)
        #print(response.status_code)
        item_dict = json.loads(response.text)
        try:
            # catalogs have different paths to access preview img
            if stac_source == 'planetary_computer_collections':
                item_dict['img_link'] = item_dict.get('assets', {}).get('rendered_preview', {}).get('href')
            elif stac_source == 'geoservice_collections':
                item_dict['img_link'] = item_dict.get('assets', {}).get('thumbnail', {}).get('href')
            else:
                # item not available for terrabyte stac items
                item_dict['img_link'] = None            
        except Exception as e:
            print(e)
            print("failed to load rendered preview (planetary computer)")
            item_dict['img_link'] = None
        items_list.append(item_dict)
    return items_list


def create_stac_export_notebook(db, graph_name:str, stac_collection_id:str, location_filters, time_interval, stac_source_dict:dict):
    ''' 
        Similar function as "make_stac_item_query" but generates a IPython notebook to export it 
    '''
    stac_source = get_stac_source(stac_collection_id=stac_collection_id, graph_name=graph_name, db=db)
    print(stac_source)
    api_link = stac_source_dict[stac_source]['api_link']

    # prepare location filters
    location_filters = get_geojson_from_location_filters(location_filters)
    coordinates = location_filters['coordinates']
    time_interval = get_time_interval(time_interval, to_string=True)
    print("------------")
    print(stac_source)
    print(api_link)
    print(location_filters)
    print(time_interval)
    
    # TODO create python notebook 
    template_notebook = nbf.read('assets/STAC_notebook_template.ipynb', as_version=4)
    
    parse_block = 5
    argument_source_code = template_notebook['cells'][parse_block]['source']
    
    # modify source code
    argument_source_code = argument_source_code.replace('<<api_link>>', str(api_link))
    argument_source_code = argument_source_code.replace('<<coordinates>>', str(coordinates))
    argument_source_code = argument_source_code.replace('<<stac_collection_id>>', str(stac_collection_id))
    
    template_notebook['cells'][parse_block]['source'] = argument_source_code
    
    
    print("time arguments appending...")
    time_argument_source_code = template_notebook['cells'][parse_block+1]['source']
    if time_interval is None:
        time_argument_source_code += "\n#No time range arguments provided\ntime_range=None"
    else:
        time_argument_source_code += get_time_interval_source_code(time_interval)
    template_notebook['cells'][parse_block+1]['source'] = time_argument_source_code
    
    filepath = 'assets/custom_notebook.ipynb'
    nbf.write(template_notebook, filepath)
    return filepath
    
    
def get_time_interval_source_code(time_interval:list): 
    return f"""
date_format = '%Y-%m-%dT%H:%M:%S.%fZ'
time_start_str='{str(time_interval[0])}'
time_end_str='{str(time_interval[1])}'

time_start = datetime.strptime(time_start_str, date_format)
time_end = datetime.strptime(time_end_str, date_format)

# the actual timerange (datetime objects)
time_range = [time_start, time_end]

"""
    