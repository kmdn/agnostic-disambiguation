import json
import sparqlutils
from os import listdir
from os.path import isfile, join
import requests
#from tqdm import tqdm
from tqdm import tqdm_notebook
import json
from os import listdir
from os.path import isfile, join
from pynif import NIFCollection
from typing import List
from pathlib import Path


def generate_candidates(mention):
    endpoint_url = "https://lookup.dbpedia.org/api/search?format=JSON&query="

    response = requests.get(endpoint_url+str(mention))
    if response.status_code == 500:
        # Internal error...
        print(f"Internal error for mention[{mention}]")
        return [[], [], [], [], [], []]
    if response.status_code != 200:
        raise ValueError(f"Could not retrieve candidates for mention[{mention}], code: {response.status_code}")
    # Response to JSON
    json_candidates = json.loads(response.text)
    
    # Extract the candidate "documents" from the response JSON
    json_candidate_documents = json_candidates['docs']
    
    # Transform DBpedia JSON candidates to data structure we want to use for LLM purposes
    labels, desc, types, uris, score, refCount = transform_dbp_json_cands_to_dict(json_documents=json_candidate_documents)
    return [labels, desc, types, uris, score, refCount]

#lst_candidate_info = generate_candidates("Steve")

def generate_candidates_and_descriptions(uris_for_descriptions=[], step=100, prefix=""):
    # uris_for_descriptions --> all URIs we want to crawl
    # cands_desc
    uris_for_descriptions_crawled = set()
    for filename in range(0, len(uris_for_descriptions), step):
        print("Working on range[%d, %d]" % (filename, filename+step))
        dict_uri_desc = sparqlutils.query_descriptions_multiple_uris(uris_for_descriptions[filename:filename+step])
        save_cand_desc_result(cand_desc_dictionary=dict_uri_desc, file_counter=prefix+str(filename))
        uris_for_descriptions_crawled.update(set(dict_uri_desc.keys()))
    print("%d URIs crawled." % len(uris_for_descriptions_crawled))
    print("%d URIs wanted." % len(uris_for_descriptions))
    print("%d URIs crawled and wanted." % len(set(uris_for_descriptions_crawled) & set(uris_for_descriptions)))
    print("%d URIs crawled but not wanted." % len(set(uris_for_descriptions_crawled) - set(uris_for_descriptions)))
    print("%d URIs wanted but not crawled." % len(set(uris_for_descriptions) - set(uris_for_descriptions_crawled)))



# Now double check whether all of the URIs we have also actually have an associated description
# If not, ... crawl the missing ones again.
def check_for_missing_uri_descriptions_and_complete(uris_for_descriptions: List, prefix: str,  result_directory: str, step=100):
    all_cand_desc_results = load_cand_desc_results(result_directory=result_directory)

    # uris_for_descriptions --> all URIs we want to crawl
    # cands_desc
    uris_for_descriptions_crawled = set()
    for filename in all_cand_desc_results:
        cands_desc = all_cand_desc_results[filename]
        #print(list(cands_desc.keys())[0])
        uris_for_descriptions_crawled.update(set(cands_desc.keys()))

    set_missing_uris = set(uris_for_descriptions) - set(uris_for_descriptions_crawled)
    lst_missing_uris = list(set_missing_uris)
    #print(lst_missing_uris[0:50])
    print(f"{len(set_missing_uris)} missing URIs (crawled: {len(set(uris_for_descriptions_crawled))}, total wanted: {len(set(uris_for_descriptions))}).")

    for i in range(0, len(lst_missing_uris), step):
        print("Working on missing range[%d, %d]" % (i, i+step))
        dict_uri_desc = sparqlutils.query_descriptions_multiple_uris(lst_missing_uris[i:i+step])
        save_cand_desc_result(cand_desc_dictionary=dict_uri_desc, file_counter=prefix+str(i), result_directory=result_directory)


def save_cand_desc_result(cand_desc_dictionary={}, \
                          result_directory="./data/candidate_descriptions/CoNLL_AIDA-YAGO2-dataset.nif/",\
                          file_counter="NA"):
    Path(result_directory).mkdir(parents=True, exist_ok=True)   
    with open(result_directory+str(file_counter)+'.json', 'w', encoding='utf-8') as f:
        json.dump(cand_desc_dictionary, f, ensure_ascii=False, indent=4)
        
def load_cand_desc_results(
                          result_directory="./data/candidate_descriptions/CoNLL_AIDA-YAGO2-dataset.nif/"):
    all_cand_desc_results = {}
    for path in [result_directory+f for f in listdir(result_directory) if isfile(join(result_directory, f))]:
        with open(path, encoding='utf-8') as json_file:
            in_json = json.load(json_file)
            
            all_cand_desc_results[path] = in_json
    return all_cand_desc_results


def save_candidate_result(cand_dictionary={}, \
                          result_directory="./data/candidates/CoNLL_AIDA-YAGO2-dataset.nif/",\
                          file_counter="NA"):
    with open(result_directory+str(file_counter)+'.json', 'w', encoding='utf-8') as f:
        json.dump(cand_dictionary, f, ensure_ascii=False, indent=4)
        

def load_candidate_results(
                          result_directory="./data/candidates/CoNLL_AIDA-YAGO2-dataset.nif/"):
    all_candidate_results = {}
    for path in [result_directory+f for f in listdir(result_directory) if isfile(join(result_directory, f))]:
        with open(path, encoding='utf-8') as json_file:
            in_json = json.load(json_file)
            
            all_candidate_results[path] = in_json
    return all_candidate_results


def transform_dbp_json_cands_to_dict(json_documents={}):
    candidate_dict = {}
    candidate_dict['types'] = []
    candidate_dict['label'] = []
    candidate_dict['desc'] = []
    candidate_dict['uri'] = []
    candidate_dict['score'] = []
    candidate_dict['refCount'] = []
    
    for i in range(len(json_documents)):
        document = json_documents[i]
        try:
            # Retrieve information
            # Description
            small_desc = document.get('comment', "")
            # Types for this candidate
            types = document.get('typeName', [])
            if types is None:
                #print(f"No types for: {document.keys()}, {document['label']}")
                types = ""
                
            # The label / name for this candidate
            label = document.get('label', [])
            
            # URI for this candidate
            uri = document.get('resource', [])

            # Score (Optional)
            score = document.get('score', [])

            # Reference Count (Optional)
            refCount = document.get('refCount', [])

            # Populate information
            candidate_dict['types'].append(types)
            candidate_dict['label'].extend(label)
            candidate_dict['desc'].extend(small_desc)
            candidate_dict['uri'].extend(uri)
            candidate_dict['score'].extend(score)
            candidate_dict['refCount'].extend(refCount)

            
        except:
            print(f"ERROR: {document.keys()}")
            raise
    return candidate_dict['label'], candidate_dict['desc'], candidate_dict['types'], candidate_dict['uri'], candidate_dict['score'], candidate_dict['refCount']


# Generate dictionary of results that will be persisted for generating prompts from
def compute_save_candidates_for_mentions(result_directory="./data/candidates/CoNLL_AIDA-YAGO2-dataset.nif/", collection: NIFCollection = None):
# Check which are done in directory so we don't redo them
    Path(result_directory).mkdir(parents=True, exist_ok=True)
    # to find what is where & avoid redoing
    mapping_path_document = {}
    for path in [result_directory+f for f in listdir(result_directory) if isfile(join(result_directory, f))]:
        with open(path, encoding='utf-8') as json_file:
            in_json = json.load(json_file)
        key = list(dict(in_json).keys())[0]
        mapping_path_document[key] = path

    file_counter = len(mapping_path_document)
    # To see how many were skipped
    skip_counter = 0
    
    for context in tqdm_notebook(collection.contexts, position=0):
        mapping_document_candidate_info = {}

        # See what can be called on context
        # print(dir(context))

        # document/context.mention = input sentence (1 document = 1 sentence)
        document = context.mention
        # If it's done already, continue to next
        if document in mapping_path_document.keys():
            skip_counter += 1
            continue

        # Document string will be used as key for all candidate information
        #print(f"Processing document: {document}")
        #print(f"Context: {context.phrases}")
        key = document

        mentions = []

        doc_labels = []
        doc_desc = []
        doc_types = []
        doc_candidate_uris = []
        doc_scores = []
        doc_refCount = []
        doc_true_uris = []
        doc_begin_index = []
        doc_end_index = []


        #print(f"{context.mention}, {context.beginIndex}, {context.endIndex}")
        # 1 phrase = 1 mention
        for phrase in tqdm_notebook(context.phrases, position=1):
            #print(phrase)
            #print(dir(phrase))
            #print(f"{phrase.mention}, {phrase.beginIndex}, {phrase.endIndex}, {phrase.generated_uri}, {phrase.taClassRef}, {phrase.taIdentRef}")
            lst_candidate_info = generate_candidates(phrase.mention)
            labels = lst_candidate_info[0]
            desc = lst_candidate_info[1]
            types = lst_candidate_info[2]
            candidate_uris = lst_candidate_info[3]
            scores = lst_candidate_info[4]
            refCount = lst_candidate_info[5]
            # Single URI
            true_uri = phrase.taIdentRef

            # Add data for persistence
            # always single entry per mention --> extend
            # multiple entries per mention    --> append
            mentions.append(phrase.mention)
            doc_labels.append(labels)
            doc_desc.append(desc)
            doc_types.append(types)
            doc_candidate_uris.append(candidate_uris)
            doc_scores.append(scores)
            doc_refCount.append(refCount)
            # Single URI
            doc_true_uris.append(true_uri)
            doc_begin_index.append(phrase.beginIndex)
            doc_end_index.append(phrase.endIndex)

        #print(f"Mentions: {mentions}")
        # Once all phrases aka. mentions for a sentence are done, store the sentence information
        mapping_document_candidate_info[key] = {
            'mentions' : mentions,#
            'begin_index' : doc_begin_index,#
            'end_index' : doc_end_index,#
            'labels' : doc_labels,#
            'desc' : doc_desc,#
            'types' : doc_types,#
            'candidate_uris' : doc_candidate_uris,#
            'scores' : doc_scores,#
            'refCount' : doc_refCount,#
            'true_uris' : doc_true_uris,#
        }

        # Save results since sentence has been processed

        save_candidate_result(cand_dictionary=mapping_document_candidate_info, result_directory=result_directory, file_counter=file_counter)
        file_counter+=1
        #if file_counter >= 2:
        #    break

    print(f"Finished processing {file_counter} documents, skipped {skip_counter}.")

def populate_candidate_description_dict():
    all_cand_desc_results = load_cand_desc_results()

    uris_for_descriptions_crawled = {}
    for filename in all_cand_desc_results:
        cands_desc = all_cand_desc_results[filename]
        #print(list(cands_desc.keys())[0])
        for key in cands_desc:
            uris_for_descriptions_crawled[key] = cands_desc[key]
    return uris_for_descriptions_crawled
