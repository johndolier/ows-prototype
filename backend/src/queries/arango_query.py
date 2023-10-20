from pyArango.connection import DBHandle
from utils import normalize_scoring_range
from sentence_transformers import SentenceTransformer


ALL_KEWORDS_QUERY = """
FOR v in Keyword
    RETURN v
"""

EO_OBJECTS_FROM_NODE_QUERY = """
FOR v in OUTBOUND @node_id Mentions
    RETURN v._id
"""

NODE_FROM_KEYWORD_QUERY = """
LET keyword = @keyword

FOR v in INBOUND keyword HasKeyword
    RETURN v._id
"""



'''
SIMPLE_PUB_ARANGOSEARCH_QUERY:
    query: keyword query
    limit: maximum number of documents to return (not used currently)
    sim_score: controls the strictness of the matching (high sim_score -> only nodes that really match the keyword query are returned) [0,1]

    Returns publication nodes that are similar to the query; uses arangosearch indexing (ngrams, levenshtein distance) for search
'''
SIMPLE_PUB_ARANGOSEARCH_QUERY = """
LET query = @query
LET sim_score = @sim_score

LET phraseStructure = (
    FOR tok IN TOKENS(query, 'text_en')
        RETURN {
            "LEVENSHTEIN_MATCH": [
                tok,
                1,
                false
            ]
        }
)

LET pubs_fuzzy = (
    FOR v IN publications_view
        SEARCH NGRAM_MATCH(v.title, query, sim_score, 'fuzzy_search_bigram')
        OR BOOST(PHRASE(v.title, phraseStructure, 'en_tokenizer'), 10)
        OR BOOST(PHRASE(v.abstract, phraseStructure, 'en_tokenizer'), 10)
        SORT BM25(v) DESC  
        RETURN {pub:v, score: BM25(v)}
)

FOR node in pubs_fuzzy 
    LET conn_eo_objects = (
        FOR v in OUTBOUND node.pub._id Mentions
            RETURN v._id
    )

    RETURN {pub:node.pub, score:node.score, eo_objects:conn_eo_objects}
    
"""

'''
SIMPLE_STAC_ARANGOSEARCH_QUERY:
    query: keyword query
    limit: maximum number of documents to return
    sim_score: controls the strictness of the matching (high sim_score -> only nodes that really match the keyword query are returned) [0,1]

    Returns STAC collection nodes that are similar to the query; uses arangosearch indexing (ngrams, levenshtein distance) for search
'''
SIMPLE_STAC_ARANGOSEARCH_QUERY = """
LET query = @query
LET sim_score = @sim_score

LET phraseStructure = (
    FOR tok IN TOKENS(query, 'text_en')
        RETURN {
            "LEVENSHTEIN_MATCH": [
                tok,
                3,
                false
            ]
        }
    )

LET stac_fuzzy = (
    FOR v IN stac_view
        SEARCH NGRAM_MATCH(v.title, query, sim_score, 'fuzzy_search_bigram')
            OR BOOST(PHRASE(v.title, phraseStructure, 'en_tokenizer'), 10)
            OR BOOST(PHRASE(v.description, phraseStructure, 'en_tokenizer'), 10)
        SORT BM25(v) DESC  
        LIMIT @limit
        RETURN {stac:v, score: BM25(v)}
)

FOR node in stac_fuzzy 
    LET conn_eo_objects = (
        FOR v in OUTBOUND node.stac._id Mentions
            RETURN v._id
    )
    RETURN {stac:node.stac, score:node.score, eo_objects:conn_eo_objects}
"""


'''
SIMPLE_STAC_EMB_QUERY:
    query_embedding: list of floats (embedding) from SentenceTransformer model
    limit: maximum number of documents to return
    sim_threshold: threshold to cut of for cosine similarity

    Returns STAC collection nodes that are similar to the query; uses text embedding vector similarity for search (semantic search)
    + searches for connected EO objects
'''
SIMPLE_STAC_EMB_QUERY = """
    LET query_emb = @query_embedding

    LET query_emb_size = (SQRT(SUM(
        FOR k IN RANGE(0,768)
            RETURN POW(TO_NUMBER(NTH(query_emb, k)), 2)
    )))

    LET stac_fuzzy = (
        FOR v in STACCollection
            LET v_size = (SQRT(SUM(
                FOR k IN RANGE(0,768)
                    RETURN POW(TO_NUMBER(NTH(v.text_embedding, k)), 2)
            )))

            LET numerator = (SUM(
                FOR i in RANGE(0,768)
                    RETURN TO_NUMBER(NTH(query_emb, i)) * TO_NUMBER(NTH(v.text_embedding, i))
            ))

            LET cos_sim = (numerator)/(query_emb_size*v_size)
            FILTER cos_sim >= @sim_threshold
            SORT cos_sim DESC
            //LIMIT @limit 
            RETURN {stac: v, score:cos_sim}
    )

    FOR node in stac_fuzzy 
        LET conn_eo_objects = (
            FOR v in OUTBOUND node.stac._id Mentions
                RETURN v._id
        )
        RETURN {stac:node.stac, score:node.score, eo_objects:conn_eo_objects}
"""

'''
SIMPLE_PUB_EMB_QUERY:
    query_embedding: list of floats (embedding) from SentenceTransformer model
    limit: maximum number of documents to return

    Returns Publication nodes that are similar to the query; uses text embedding vector similarity for search (semantic search)
    Note: low performance; too many Publication nodes to compute vector similarity in ArangoDB query!
'''
SIMPLE_PUB_EMB_QUERY = """
    LET query_emb = @query_embedding

    LET query_emb_size = (SQRT(SUM(
        FOR k IN RANGE(0,768)
            RETURN POW(TO_NUMBER(NTH(query_emb, k)), 2)
    )))

    FOR v in Publication
        LET v_size = (SQRT(SUM(
            FOR k IN RANGE(0,768)
                RETURN POW(TO_NUMBER(NTH(v.text_embedding, k)), 2)
        )))

        LET numerator = (SUM(
            FOR i in RANGE(0,768)
                RETURN TO_NUMBER(NTH(query_emb, i)) * TO_NUMBER(NTH(v.text_embedding, i))
        ))

        LET cos_sim = (numerator)/(query_emb_size*v_size)

        SORT cos_sim DESC
        LIMIT @limit
        RETURN {pub: v, score:cos_sim}
"""


'''
REFINED_EMB_QUERY
    query_embedding: list of floats (embedding) from SentenceTransformer model
    node_id_list: list of ID's to use for search
    sim_threshold: threshold for the similarity score
    limit: maximum number of documents to return

    Takes a list of ID's and computes a similarity score to the query embedding, 
    Ranks and limits the documents according to the parameters
'''
REFINED_EMB_QUERY = """
    LET query_emb = @query_embedding

    LET query_emb_size = (SQRT(SUM(
        FOR k IN RANGE(0,768)
            RETURN POW(TO_NUMBER(NTH(query_emb, k)), 2)
    )))

    FOR id in node_id_list
        LET v = DOCUMENT(id)
        LET v_size = (SQRT(SUM(
            FOR k IN RANGE(0,768)
                RETURN POW(TO_NUMBER(NTH(v.text_embedding, k)), 2)
        )))

        LET numerator = (SUM(
            FOR i in RANGE(0,768)
                RETURN TO_NUMBER(NTH(query_emb, i)) * TO_NUMBER(NTH(v.text_embedding, i))
        ))

        LET cos_sim = (numerator)/(query_emb_size*v_size)
        FILTER cos_sim >= sim_threshold
        SORT cos_sim DESC
        LIMIT @limit
        RETURN {node: v, score:cos_sim}
"""


'''
KEYWORD_CONNECTION_COUNT_QUERY:
    input: general keyword to search for
    target_collection: collections to return (either "STACCollection" or "Publication")
    keyword_sim_score: similarity score for matching keyword nodes
    concept_sim_score: similarity score for matching concept nodes
    limit: limits the number of keywords/concept nodes that match the keyword

    1) Searches for similar Keyword and OAConceptAnnotation nodes that match the input; 
    2) Collects nodes that are connected to the retrieved Keywords/Concepts (+ counts the number of connections)
    3) Returns two list of ID's (+ their counts) relative to Keyword and Concept connections
'''
KEYWORD_CONNECTION_COUNT_QUERY = """
LET query = @input

LET phraseStructure = (FOR tok IN TOKENS(query, 'text_en')
    RETURN {
      "LEVENSHTEIN_MATCH": [
        tok,
        2,
        false
      ]
    })

LET matchingKeywords = (
    FOR v IN keyword_view
        SEARCH NGRAM_MATCH(v.keyword_full, query, @keyword_sim_score, 'fuzzy_search_bigram')
            OR
            BOOST(PHRASE(v.keyword_full, phraseStructure, 'en_tokenizer'), 10)
        SORT BM25(v) DESC
        LIMIT @limit
        RETURN {keyword: v}
)

LET matchingConcepts = (
    FOR v IN concept_annotation_view
        SEARCH NGRAM_MATCH(v.name, query, @concept_sim_score, 'fuzzy_search_bigram')
            OR
            BOOST(PHRASE(v.name, phraseStructure, 'en_tokenizer'), 10)
        SORT BM25(v) DESC
        LIMIT @limit
        RETURN {concept: v}
)

LET conceptCount = (
    FOR conceptNode in matchingConcepts
        FOR vertexNode in 1..1 INBOUND conceptNode.concept._id HasOAConceptAnnotation
        FILTER IS_SAME_COLLECTION(@target_collection, vertexNode._id) 
        COLLECT id = vertexNode._id WITH COUNT INTO length
        SORT length DESC
        RETURN {id: id, conceptCount: length}
)

LET keywordCount = (
    FOR conceptNode in matchingKeywords
        FOR vertexNode in 1..1 INBOUND conceptNode.keyword._id HasKeyword
        FILTER IS_SAME_COLLECTION(@target_collection, vertexNode._id) 
        COLLECT id = vertexNode._id WITH COUNT INTO length
        SORT length DESC
        RETURN {id: id, keywordCount: length}
)

RETURN {conceptCount: conceptCount, keywordCount: keywordCount}

"""


def get_all_keywords(db: DBHandle, batchSize:int = 100) -> list[str]: 
    try:
        result = db.AQLQuery(ALL_KEWORDS_QUERY, batchSize=batchSize, rawResults=True)
        result = [key for key in result] # transform query object to list of keywords
    except Exception as e:
        print(e)
        result = []
    return result

def make_publications_query(db: DBHandle, graph_name:str, query:str, keywords:list[str] = None, limit:int = 500) -> list[dict]:
    ''' 
        Fetches Publication nodes according to query and keywords (list)
    '''

    # create query string from keywords
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
        result = db.AQLQuery(SIMPLE_PUB_ARANGOSEARCH_QUERY, bindVars=query_params, rawResults=True)
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

def make_stac_collection_query(db: DBHandle, graph_name:str, query:str, keywords:list[str] = None, limit:int = 200) -> list[dict]:
    # returns stac collections that are most likely to match query
    # TODO automatically get connected eo missions/instruments

    # create query string from keywords
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
        result = db.AQLQuery(SIMPLE_STAC_EMB_QUERY, bindVars=query_params, rawResults=True)
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

def get_nodes_from_keyword(db: DBHandle, graph_name:str, keyword:str) -> list[str]:
    # returns list of id's wich are connected with HasKeyword edge (either STACCollection or Publication)
    keyword = create_key_from_keyword(keyword=keyword.lower())
    query_params = {
        'keyword': f'Keyword/{keyword}', 
    }
    try:
        result = db.AQLQuery(NODE_FROM_KEYWORD_QUERY, bindVars=query_params, rawResults=True)
    except Exception as e:
        print(e)
        result = []
    return result

def get_related_eo_connections(db: DBHandle, graph_name:str, key:str, collection:str) -> list[str]:
    # returns list of id's of eo missions/instruments that are connected to given node (either STACCollection or publication)
    node_id = f"{collection}/{key}"
    query_params = {
        'node_id': node_id, 
    }
    try:
        result = db.AQLQuery(EO_OBJECTS_FROM_NODE_QUERY, bindVars=query_params, rawResults=True)
    except Exception as e:
        print(e)
        result = []
    return result



### HELPER Functions

# note: function is copied from other project 
# TODO link function in case of change
def create_key_from_keyword(keyword:str) -> str:
    # keyword argument should already be lowercase!
    import re
    try:
        new_key = re.sub('[^A-Za-z0-9]+', '', keyword).strip()
        return new_key
    except:
        return None
    



