from SPARQLWrapper import SPARQLWrapper, JSON, POST
from collections.abc import Callable

def build_get_description(dbpedia_subject_uri=None):
    if dbpedia_subject_uri is None:
        raise ValueError("You need to input a subject URI/IRI")
    return """
        {
            ?s dbo:abstract ?o .
            FILTER(?s = <"""+dbpedia_subject_uri+""">) . 
            FILTER(LANG(?o) = "en") .
        }
"""


def build_get_type(dbpedia_subject_uri=None):
    if dbpedia_subject_uri is None:
        raise ValueError("You need to input a subject URI/IRI")
    return """
        {
            ?s rdf:type ?o .
            FILTER(?s = <"""+dbpedia_subject_uri+""">) . 
        }
"""


def build_get_description_wikidata(wikidata_subject_uri=None):
    if wikidata_subject_uri is None:
        raise ValueError("You need to input a subject URI/IRI")
    
    wd_entity = wikidata_subject_uri.split("/")[-1]

    return f"""
        {{
            ?s schema:description ?o .
            FILTER(?s = wd:{wd_entity}) . 
            FILTER(isLiteral(?o)) .
            FILTER(langMatches(lang(?o), "en"))
        }}"""

def build_get_type_wikidata(wikidata_subject_uri=None):
    if wikidata_subject_uri is None:
        raise ValueError("You need to input a subject URI/IRI")
    
    wd_entity = wikidata_subject_uri.split("/")[-1]
    return f"""
        {{
            ?s wdt:P31 ?o .
            FILTER(?s = wd:{wd_entity}) . 
            ?s rdf:type ?o .
        }}
"""



def build_union_query(dbpedia_subject_uris=[], single_query_function: Callable[[str], str]=build_get_description):
    if dbpedia_subject_uris is None:
        raise ValueError("You need to input a subject URI/IRI")
    
    for uri in dbpedia_subject_uris:
        if not uri.startswith("http://") and not uri.startswith("https://"):
            raise ValueError("Not a valid URI/IRI: " + uri)

    union_query_start = """
    SELECT DISTINCT ?s ?o
    WHERE
    {
    """
    center_query = ""
    union_query_end = "}"

    # Take the first element separately... makes it a lot easier for the logic
    center_query += single_query_function(str(dbpedia_subject_uris[0]))

    for idx in range(1, len(dbpedia_subject_uris)):
        uri = str(dbpedia_subject_uris[idx])
        center_query += """
        UNION
        """
        center_query += single_query_function(uri)
    return union_query_start + center_query + union_query_end


def build_union_query_get_description(dbpedia_subject_uris=[]):
    return build_union_query(dbpedia_subject_uris, single_query_function=build_get_description)


def query_multiple_uris(uris_for_descriptions=[], single_query_function: Callable[[str], str]=build_get_description):
    '''Note that DBpedia's SPARQL endpoint can only handle 10k output - so definitely make it smaller than that.'''
    query = build_union_query(uris_for_descriptions, single_query_function=single_query_function)

    sparql = SPARQLWrapper(endpoint="https://dbpedia.org/sparql", returnFormat=JSON)
    sparql.setMethod(POST)

    sparql.setQuery(query)

    dict_uri_desc = {}

    try:
        ret = sparql.queryAndConvert()


        for r in ret["results"]["bindings"]:
            uri = r['s']['value']
            obj = r['o']['value']
            # Check if there is sth already
            uris_in_dict = dict_uri_desc.get(uri, [])
            uris_in_dict.append(obj)
            dict_uri_desc[uri] = uris_in_dict
    except Exception as e:
        print("[ERROR QUERYING]: ",e)

    return dict_uri_desc

def query_descriptions_multiple_uris(uris_for_descriptions=[], sparql_endpoint="https://dbpedia.org/sparql"):
    '''Note that DBpedia's SPARQL endpoint can only handle 10k output - so definitely make it smaller than that.'''
    query = build_union_query_get_description(uris_for_descriptions)

    sparql = SPARQLWrapper(endpoint=sparql_endpoint, returnFormat=JSON)
    sparql.setMethod(POST)

    # test_query = """
    #     SELECT DISTINCT ?s ?desc
    #     WHERE
    #     {
    #         { 
    #             ?s dbo:abstract ?desc .
    #             FILTER(?s = <http://dbpedia.org/resource/Steve_Jobs>) . 
    #             FILTER(LANG(?desc) = "en") .
    #         }
    #         UNION
    #         { 
    #             ?s dbo:abstract ?desc .
    #             FILTER(?s = <http://dbpedia.org/resource/Steve_Wozniak>) . 
    #             FILTER(LANG(?desc) = "en") .
    #         }
    #     }
    #     """

    sparql.setQuery(query)

    dict_uri_desc = {}

    try:
        ret = sparql.queryAndConvert()


        for r in ret["results"]["bindings"]:
            uri = r['s']['value']
            desc = r['o']['value']
            dict_uri_desc[uri] = desc
    except Exception as e:
        print(f"[ERROR QUERYING]: {e}: URIS: {uris_for_descriptions}")
        #print( "Query: ", query)

    return dict_uri_desc

