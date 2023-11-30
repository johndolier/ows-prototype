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
        # invalid format!
        print(f"failed to process stac item request for request {id_str}")
        print(e)
        # bad request
        return None
    
    