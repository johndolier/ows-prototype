
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
        return db.AQLQuery(STAC_SOURCE_QUERY, bindVars=query_params, rawResults=True)[0].get('_key', None)
    except Exception as e:
        print(e)
        print(f"error - could not load stac collection node with id {stac_collection_id}")
        return None
    


def get_geojson_from_location_filters(location_filters):
    ''' Transforms the location filter geoBounds into a geojson object for querying stac catalogs '''
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

def make_stac_item_query(db, graph_name:str, stac_collection_id:str, location_filters, time_interval, limit, stac_source_dict):
    '''
        Retrieve STAC items for the given stac collection, location, time and further parameters
    '''

    stac_source = get_stac_source(stac_collection_id=stac_collection_id, graph_name=graph_name, db=db)
    api_link = stac_source_dict[stac_source]
    catalog = get_catalog(api_link, stac_source)

    items_list = []
    geojson_polygon = get_geojson_from_location_filters(location_filters)
    search_items = catalog.search(
        max_items = limit, 
        collections = stac_collection_id, 
        intersects = geojson_polygon, 
        datetime = time_interval, 
    )
    search_items = list(search_items.items())
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


def create_stac_export_notebook(db, graph_name:str, stac_collection_id:str, location_filters, time_interval:list, limit:int, stac_source_dict:dict):
    ''' 
        Similar function as "make_stac_item_query" but generates a IPython notebook to export it 
    '''
    stac_source = get_stac_source(stac_collection_id=stac_collection_id, graph_name=graph_name, db=db)
    api_link = stac_source_dict[stac_source]['api_link']
    #geojson_polygon = get_geojson_from_location_filters(location_filters)
    geojson_polygon = location_filters

    # prepare time interval
    if len(time_interval==1):
        pass
    elif len(time_interval==2):
        pass
    else:
        print(f"error - {time_interval} must have 1 or 2 datetime elements!")
        time_interval = None

    # TODO create python notebook    
    template_notebook = nbf.read('assets/notebook_template.ipynb', as_version=4)

    args = {
        'api_link': api_link, 
        'stac_collection_id': stac_collection_id, 
        'location': geojson_polygon, 
        'time': time_interval, 
        'item_limit': limit, 
    }

    for cell in template_notebook['cells']:
        for key, value in args.items():
            cell['source'] = cell['source'].replace(f'{{{{{key}}}}}', str(value))
            pass
    nbf.write(template_notebook, 'custom_notebook.ipynb')
    
