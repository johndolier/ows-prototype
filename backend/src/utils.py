# HELPER FUNCTIONS


def normalize_scoring_range(results, min_score, max_score):
    range = max_score - min_score
    for result in results:
        if range == 0:
            # set everything to 0.5
            result['score'] = 0.5
        else:
            result['score'] = (result['score'] - min_score) / range
    return results


def get_stac_collection_from_id(id_str:str):
    try:
        stac_collection_id = id_str.split('/')[1]
        return stac_collection_id
    except Exception as e:
        # we assume that the id_str is already a valid STACCollectionId (e.g. it was already split in frontend client)
        #print(f"WARNING: {e}")
        #print(f"returning id_str as is: {id_str}")
        return id_str
    
    