# This file is a truncated version of the original EO Knowledge graph creator project.
# It can be used to initialize the graph in an already existing ArangoDB database and create search views for the final application
# Author: Johannes Honeder
# Last changed: 23.11.2023



from cag.graph_elements.nodes import GenericOOSNode, Field
from cag.graph_elements.relations import GenericEdge
from cag.framework.creator.base_creator import GraphCreatorBase

from cag.view_wrapper.arango_analyzer import ArangoAnalyzer, AnalyzerList
from cag.view_wrapper.link import Link, Field as ViewField
from cag.view_wrapper.view import View



class EOMission(GenericOOSNode):
    _name = "EOMission"
    _fields = {
        'mission_name_short': Field(), 
        'mission_name_full': Field(), 
        'description': Field(), 
        'mission_agencies': Field(), 
        'mission_site': Field(), 
        'data_access_portal': Field(), 
        **GenericOOSNode._fields, 
    }

class EOInstrument(GenericOOSNode):
    _name = "EOInstrument"
    _fields = {
        'instrument_name_short': Field(), 
        'instrument_name_full': Field(), 
        'description': Field(), 
        'instrument_agencies': Field(), 
        'instrument_status': Field(), 
        'instrument_type': Field(), 
        'instrument_technology': Field(), 
        'waveband_categories': Field(), 
        **GenericOOSNode._fields, 
    }

class Author(GenericOOSNode):
    _name = "Author"
    _fields = {
        'id': Field(), 
        'first_name': Field(), 
        'last_name': Field(), 
        'elib_id': Field(), 
        **GenericOOSNode._fields, 
    }

class Publication(GenericOOSNode):
    _name = "Publication"
    _fields = {
        'id': Field(), 
        'title': Field(), 
        'abstract': Field(), 
        'type': Field(), 
        'date': Field(), 
        'eprint_status': Field(), 
        'keywords': Field(), 
        #'creators': Field(), 
        **GenericOOSNode._fields, 
    }

class STACSource(GenericOOSNode):
    _name = "STACSource"
    _fields = {
        'id': Field(), 
        'name': Field(), 
        'api_link': Field(),
        'href': Field(),
        # TODO add additional information for STAC sources
    }

class STACCollection(GenericOOSNode):
    _name = "STACCollection"
    _fields = {
        'id': Field(), 
        'type': Field(), 
        'description': Field(), 
        'title': Field(), 
        'extent': Field(), 
        'keywords': Field(), 
        'summaries': Field(), 
        'links': Field(), 
        'providers': Field(), 
        'assets': Field(), 
        **GenericOOSNode._fields, 
    }


class Keyword(GenericOOSNode):
    _name = "Keyword"
    _fields = {
        'keyword_full': Field(), 
        **GenericOOSNode._fields, 
    }


class HasKeyword(GenericEdge):
    _fields = GenericEdge._fields

class HasAuthor(GenericEdge):
    _fields = GenericEdge._fields

class Mentions(GenericEdge):
    _fields = GenericEdge._fields

class IsEquippedWith(GenericEdge):
    _fields = GenericEdge._fields

class SourceContains(GenericEdge):
    _fields = GenericEdge._fields

class STACSourceContains(GenericEdge):
    _fields = GenericEdge._fields


class EOGraphCreator(GraphCreatorBase):
    _name = "KG Graph"
    _description = "Earth Observation Knowledge Graph"

    _EO_MISSION_NODE = EOMission.__name__
    _EO_INSTRUMENT_NODE = EOInstrument.__name__
    _AUTHOR_NODE = Author.__name__
    _PUBLICATION_NODE = Publication.__name__
    _STAC_SOURCE_NODE = STACSource.__name__
    _STAC_COLLECTION_NODE = STACCollection.__name__
    _KEYWORD_NODE = Keyword.__name__

    _IS_EQUIPPED_WITH_RELATION = IsEquippedWith.__name__
    _SOURCE_CONTAINS_RELATION = SourceContains.__name__
    _STAC_SOURCE_CONTAINS_RELATION = STACSourceContains.__name__
    _MENTIONS = Mentions.__name__
    _HAS_KEYWORD_RELATION = HasKeyword.__name__
    _HAS_AUTHOR_RELATION = HasAuthor.__name__

    _edge_definitions = [
        {
            'relation': _IS_EQUIPPED_WITH_RELATION, 
            'from_collections': [
                _EO_MISSION_NODE, 
            ], 
            'to_collections': [
                _EO_INSTRUMENT_NODE, 
            ], 
        }, 
        {
            'relation': _SOURCE_CONTAINS_RELATION, 
            'from_collections': [
                GraphCreatorBase._CORPUS_NODE_NAME, 
            ], 
            'to_collections': [
                _EO_MISSION_NODE, 
                _EO_INSTRUMENT_NODE, 
                _PUBLICATION_NODE, 
            ], 
        }, 
        {
            'relation': _STAC_SOURCE_CONTAINS_RELATION, 
            'from_collections': [
                _STAC_SOURCE_NODE, 
            ], 
            'to_collections': [
                _STAC_COLLECTION_NODE, 
            ], 
        }, 
        {
            'relation': _MENTIONS, 
            'from_collections': [
                _PUBLICATION_NODE, 
                _STAC_COLLECTION_NODE, 
            ], 
            'to_collections': [
                _EO_MISSION_NODE, 
                _EO_INSTRUMENT_NODE, 
            ]
        }, 
        {
            'relation': _HAS_KEYWORD_RELATION, 
            'from_collections': [
                _PUBLICATION_NODE, 
                _STAC_COLLECTION_NODE, 
            ], 
            'to_collections': [
                _KEYWORD_NODE, 
            ]
        }, 
        {
            'relation': _HAS_AUTHOR_RELATION, 
            'from_collections': [
                _AUTHOR_NODE, 
            ], 
            'to_collections': [
                _PUBLICATION_NODE
            ]
        }, 
    ]


    def init_graph(self):
        pass

    def create_search_views(self):
        print(f"Start to create Analyzers and all possible views for graph {self._name}")
        try:
            print(f"creating analyzers for Arangosearch...")
            self.create_analyzers()
            print(f"Successfully created analyzers!")
        except Exception as e:
            print(f"Warning - Something went wrong when creating analyzers!")
            print(e)
        
        self.create_pub_view()
        self.create_stac_view()
        self.create_keyword_view()
        self.create_concept_annotation_view()
        self.create_keyterm_annotation_view()

        print(f"Finished creating all views!")
        

    def create_analyzers(self):
        # from https://gitlab.com/opensearch-dlr/opensearch-flows
        # create view for searching the KG

        analyzer_ngram = ArangoAnalyzer("fuzzy_search_bigram")
        analyzer_ngram.set_edge_ngrams(max=3)
        analyzer_ngram.type = ArangoAnalyzer._TYPE_NGRAM
        analyzer_ngram.set_features()

        analyzer_ngram.create(self.arango_db)

        analyzer_token = ArangoAnalyzer("en_tokenizer")
        analyzer_token.set_stopwords(include_default=False)
        analyzer_token.stemming = True
        analyzer_token.accent = False
        analyzer_token.type = ArangoAnalyzer._TYPE_TEXT
        analyzer_token.set_features()

        analyzer_token.create(self.arango_db)

    def create_pub_view(self):
        print("start creating pub view")

        # Create Publication Link - a view can have 0 to * links
        pub_link = Link(name="Publication")  # Name of a collection in the database
        linkAnalyzers = AnalyzerList(
            ["fuzzy_search_bigram", "en_tokenizer"])
        pub_link.analyzers = linkAnalyzers

        # A link can have 0..* fields
        # text_en is a predifined analyzer from arango
        title_field = ViewField("title", AnalyzerList(
            ["fuzzy_search_bigram", "en_tokenizer"]))
        abstract_field = ViewField("abstract", AnalyzerList(
            ["fuzzy_search_bigram", "en_tokenizer"]))

        pub_link.add_field(title_field)
        pub_link.add_field(abstract_field)

        # create view
        view = View('publications_view',
                    view_type="arangosearch")
        # add the link (can have 0 or 1 link)
        view.add_link(pub_link)

        # can have 0..* primary sort
        view.add_primary_sort("title", asc=False)
        view.add_stored_value(["title"], compression="lz4")
        try:
            view.create(self.arango_db)
            print("Succesfully created pub view!")
        except Exception as e:
            print("Error creating pub view, please delete the one on DB?", e)
            raise e

    def create_stac_view(self):
        print("start creating stac view")
        stac_link = Link(name="STACCollection")  # Name of a collection in the database
        linkAnalyzers = AnalyzerList(
            ["fuzzy_search_bigram", "en_tokenizer"])
        stac_link.analyzers = linkAnalyzers

        # text_en is a predifined analyzer from arango
        title_field = ViewField("title", AnalyzerList(
            ["fuzzy_search_bigram", "en_tokenizer"]))
        description_field = ViewField("description", AnalyzerList(
            ["fuzzy_search_bigram", "en_tokenizer"]))

        stac_link.add_field(title_field)
        stac_link.add_field(description_field)

        # create view
        view = View('stac_view',
                    view_type="arangosearch")
        # add the link (can have 0 or 1 link)
        view.add_link(stac_link)

        # can have 0..* primary sort
        view.add_primary_sort("title", asc=False)
        view.add_stored_value(["title"], compression="lz4")
        try:
            view.create(self.arango_db)
            print("Succesfully created stac view!")
        except Exception as e:
            print("Error creating stac view, please delete the one on DB?", e)
            raise e

    def create_keyword_view(self):
        print("start creating keyword view")

        keyword_link = Link(name="Keyword")  # Name of a collection in the database
        linkAnalyzers = AnalyzerList(
            ["fuzzy_search_bigram", "en_tokenizer"])
        keyword_link.analyzers = linkAnalyzers

        # text_en is a predifined analyzer from arango
        keyword_field = ViewField("keyword_full", AnalyzerList(
            ["fuzzy_search_bigram", "en_tokenizer"]))

        keyword_link.add_field(keyword_field)

        # create view
        view = View('keyword_view',
                    view_type="arangosearch")
        # add the link (can have 0 or 1 link)
        view.add_link(keyword_link)

        # can have 0..* primary sort
        view.add_primary_sort("keyword_full", asc=False)
        view.add_stored_value(["keyword_full"], compression="lz4")
        try:
            view.create(self.arango_db)
            print("Succesfully created keyword view!")
        except Exception as e:
            print("Error creating keyword view, please delete the one on DB?", e)
            raise e

    def create_concept_annotation_view(self):
        print("start creating concept annotation view")

        concept_link = Link(name="OAConceptAnnotationNode")  # Name of a collection in the database
        linkAnalyzers = AnalyzerList(
            ["fuzzy_search_bigram", "en_tokenizer"])
        concept_link.analyzers = linkAnalyzers

        # text_en is a predifined analyzer from arango
        concept_name_field = ViewField("name", AnalyzerList(
            ["fuzzy_search_bigram", "en_tokenizer"]))

        concept_link.add_field(concept_name_field)

        # create view
        view = View('concept_annotation_view',
                    view_type="arangosearch")
        # add the link (can have 0 or 1 link)
        view.add_link(concept_link)

        # can have 0..* primary sort
        view.add_primary_sort("name", asc=False)
        view.add_stored_value(["name"], compression="lz4")
        try:
            view.create(self.arango_db)
            print("Succesfully created concept_annotation view!")
        except Exception as e:
            print("Error creating concept annotation view, please delete the one on DB?", e)
            raise e

    def create_keyterm_annotation_view(self):
        print("start creating keyterm annotation view")

        keyterm_link = Link(name="KeyTermAnnotationNode")  # Name of a collection in the database
        linkAnalyzers = AnalyzerList(
            ["fuzzy_search_bigram", "en_tokenizer"])
        keyterm_link.analyzers = linkAnalyzers

        # text_en is a predifined analyzer from arango
        keyterm_field = ViewField("term", AnalyzerList(
            ["fuzzy_search_bigram", "en_tokenizer"]))

        keyterm_link.add_field(keyterm_field)

        # create view
        view = View('keyterm_annotation_view',
                    view_type="arangosearch")
        # add the link (can have 0 or 1 link)
        view.add_link(keyterm_link)

        # can have 0..* primary sort
        view.add_primary_sort("term", asc=False)
        view.add_stored_value(["term"], compression="lz4")
        try:
            view.create(self.arango_db)
            print("Succesfully created keyterm annotation view!")
        except Exception as e:
            print("Error creating keyterm annotation view, please delete the one on DB?", e)
            raise e