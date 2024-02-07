
# FILE HOSTS SEVERAL QUERY STRINGS FOR ARANGODB



STAC_SOURCE_QUERY = """
FOR stac_coll in STACCollection
    FILTER stac_coll._key == @doc_id
    FOR v in 1..1 INBOUND stac_coll GRAPH @graph_name
        FILTER v._id LIKE "STACSource/%"
        return v
"""


ALL_KEYWORDS_QUERY = """
FOR v in Keyword
    RETURN v
"""

ALL_AUTHORS_QUERY = """
FOR v in Author
    RETURN v
"""

ALL_EO_NODES_QUERY = """
LET eo_missions = (
    FOR v in EOMission
        return {id:v._id, name:v.mission_name_short}
)

LET eo_instruments = (
    FOR v in EOInstrument
        return {id:v._id, name:v.instrument_name_short}
)

LET eo = UNION_DISTINCT(eo_missions, eo_instruments)

FOR node in eo
    return {id: node.id, name: node.name}

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
            RETURN {node: v}
    )
    
    LET authors = (
        FOR v in INBOUND node.pub._id HasAuthor
            RETURN {author: v}
    )
    
    LET keywords = (
        FOR v in OUTBOUND node.pub._id HasKeyword 
            RETURN {keyword: v}
    )

    RETURN {pub:node.pub, score:node.score, eo_objects:conn_eo_objects, authors:authors, keywords:keywords}
    
"""

'''
SIMPLE_STAC_ARANGOSEARCH_QUERY:
    query: keyword query
    limit: maximum number of documents to return (not used currently)
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
        // LIMIT @limit
        RETURN {stac:v, score: BM25(v)}
)

FOR node in stac_fuzzy 
    LET conn_eo_objects = (
        FOR v in OUTBOUND node.stac._id Mentions
            RETURN {node: v}
    )
    LET stac_source = (
        FOR v in INBOUND node.stac._id STACSourceContains
        RETURN {name: v.name, link: v.href}
    )
    
    LET keywords = (
        FOR v in OUTBOUND node.stac._id HasKeyword 
            RETURN {keyword: v}
    )
    
    RETURN {stac:node.stac, score:node.score, eo_objects:conn_eo_objects, stac_source:stac_source, keywords:keywords}
"""


'''
SIMPLE_STAC_EMB_QUERY:
    query_embedding: list of floats (embedding) from SentenceTransformer model
    limit: maximum number of documents to return (not used currently)
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
        RETURN {node: v}
    )
    LET stac_source = (
        FOR v in INBOUND node.stac._id STACSourceContains
        RETURN {name: v.name, link: v.href}
    )
    
    LET keywords = (
        FOR v in OUTBOUND node.stac._id HasKeyword 
            RETURN {keyword: v}
    )
    
    RETURN {stac:node.stac, score:node.score, eo_objects:conn_eo_objects, stac_source:stac_source, keywords:keywords}
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


'''
GRAPH_KEYWORD_STAC_QUERY:
    keyword_list: list of keywords to search for
    eo_list: list of eo missions and instruments to search for
    
    returns all STACCollections that have a connection to the given keywords/eo missions
'''
GRAPH_KEYWORD_STAC_QUERY = """
LET keyword_stac_collections = (
    FOR keyword_id in @keyword_list
        FOR v in INBOUND  keyword_id HasKeyword
            FILTER v._id LIKE "STACCollection/%"
            RETURN DISTINCT {stac:v, score:1}
)

LET eo_stac_collections = (
    FOR eo_id in @eo_list
        FOR v in INBOUND eo_id Mentions
            FILTER v._id LIKE "STACCollection/%"
            RETURN DISTINCT {stac:v, score: 1}
)

LET stac_collections = UNION_DISTINCT(keyword_stac_collections, eo_stac_collections)

FOR node in stac_collections
    LET conn_eo_objects = (
        FOR v in OUTBOUND node.stac._id Mentions
            RETURN {node: v}
    )
    LET stac_source = (
        FOR v in INBOUND node.stac._id STACSourceContains
        RETURN {name: v.name, link: v.href}
    )
    LET keywords = (
        FOR v in OUTBOUND node.stac._id HasKeyword 
            RETURN {keyword: v}
    )
    
    RETURN {stac:node.stac, eo_objects:conn_eo_objects, stac_source:stac_source, keywords:keywords}
"""

'''
GRAPH_KEYWORD_PUB_QUERY:
    keyword_list: list of keywords to search for
    author_list: list of authors to search for
    eo_list: list of eo missions and instruments to search for
    
    returns all  Publications that have a connection to the given keywords/authors/eo missions
'''
GRAPH_KEYWORD_PUB_QUERY = """
LET keyword_pubs = (
    FOR keyword_id in @keyword_list
        FOR v in INBOUND  keyword_id HasKeyword
            FILTER v._id LIKE "Publication/%"
            RETURN DISTINCT {pub:v, score: 1}
)

LET author_pubs = (
    FOR author_id in @author_list
        FOR v in OUTBOUND  author_id HasAuthor
            FILTER v._id LIKE "Publication/%"
            RETURN {pub:v, score:1}
)

LET eo_pubs = (
    FOR eo_id in @eo_list
        FOR v in INBOUND eo_id Mentions
            FILTER v._id LIKE "Publication/%"
            RETURN DISTINCT {pub:v, score: 1}
)

LET pubs = UNION_DISTINCT(keyword_pubs, author_pubs, eo_pubs)

FOR node in pubs
    LET conn_eo_objects = (
        FOR v in OUTBOUND node.pub._id Mentions
            RETURN {node: v}
    )
    LET authors = (
        FOR v in INBOUND node.pub._id HasAuthor
            RETURN {author: v}
    )
    LET keywords = (
        FOR v in OUTBOUND node.pub._id HasKeyword 
            RETURN {keyword: v}
    )
    RETURN {pub:node.pub, eo_objects:conn_eo_objects, authors:authors, keywords:keywords}
"""