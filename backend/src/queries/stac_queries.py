
import pystac_client
import planetary_computer
import geojson
import json
import requests


PC_API = "https://planetarycomputer.microsoft.com/api/stac/v1"
TERRABYTE_API = "https://stac.terrabyte.lrz.de/public/api"
GEOSERVICE_API = "https://geoservice.dlr.de/eoc/ogc/stac/v1"



STAC_SOURCE_QUERY = """
FOR stac_coll in STACCollection
    FILTER stac_coll._key == @doc_id
    FOR v in 1..1 INBOUND stac_coll GRAPH @graph_name
        FILTER v._id LIKE "STACSource/%"
        return v
"""



def get_pc_catalog():
    return pystac_client.Client.open(
        PC_API,
        modifier=planetary_computer.sign_inplace, 
    )

def get_terrabyte_catalog():
    # TERRABYTE CALATOG DOES NOT WORK AT THE MOMENT - UTF-8 ENCODING ERROR (AT LEAST UNDER WINDOWS ON MY SYSTEM)
    return pystac_client.Client.open(
        TERRABYTE_API
    )

def get_geoservice_catalog():
    return pystac_client.Client.open(
        GEOSERVICE_API
    )

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

def make_stac_item_query(db, graph_name, stac_collection_id, location_filters, time_interval, limit):
    # TODO make coordinates homogenous -> one interface for all
    # TODO find better request strategy for STAC items? 
    query_params = {
        'doc_id': stac_collection_id, 
        'graph_name': graph_name, 
        }
    try:
        # get key from first (and only) element
        stac_source = db.AQLQuery(STAC_SOURCE_QUERY, bindVars=query_params, rawResults=True)[0].get('_key', None)
    except Exception as e:
        print(e)
        print(f"error - could not load stac collection node with id {stac_collection_id}")
        return None
    if stac_source == 'geoservice_collections':
        catalog = get_geoservice_catalog()
        API = GEOSERVICE_API
    elif stac_source == 'planetary_computer_collections':
        catalog = get_pc_catalog()
        API = PC_API
    elif stac_source == 'terrabyte_collections':
        catalog = get_terrabyte_catalog()
        API = TERRABYTE_API
    else:
        print(f"error - invalid state! did not find stac source for {stac_collection_id} ({stac_source})")
        return None

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
        item_api_str = f"{API}/collections/{stac_collection_id}/items/{item.id}"
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


def create_stac_export_notebook(db, graph_name, stac_collection_id:str, location_filters, time_interval, limit):
    ''' 
        Similar function as "make_stac_item_query" but generates a IPython notebook to export it 
    '''
    query_params = {
        'doc_id': stac_collection_id, 
        'graph_name': graph_name, 
        }
    try:
        # get key from first (and only) element
        stac_source = db.AQLQuery(STAC_SOURCE_QUERY, bindVars=query_params, rawResults=True)[0].get('_key', None)
    except Exception as e:
        print(e)
        print(f"error - could not load stac collection node with id {stac_collection_id}")
        return None
    

    pass
