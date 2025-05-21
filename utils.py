from huggingface_hub import InferenceClient
from taskdefinition import TaskDefinition
from taskexample import TaskExample
from generationprompt import GenerationPrompt
import json
import pynif
from pynif import NIFCollection
from os import listdir
from os.path import isfile, join
import tqdm
import os
import json
import re



def load_nif_dataset(nif_data_path = "./data/AIDA-YAGO2-dataset.tsv_nif"):

    nif_data = ""
    parsed_collection = None
    with open(nif_data_path, 'r', encoding="utf-8") as f:
        nif_data = f.read()
        parsed_collection = NIFCollection.loads(nif_data, format='turtle')


    print("Finished reading NIF data from file(%s)." % nif_data_path)
    print(parsed_collection)
    #parsed_collection = load_nif_dataset(nif_data_path = "C:\\Users\\wf7467\\Desktop\\Evaluation Datasets\\Datasets\\entity_linking\\conll_aida-yago2-dataset\\AIDA-YAGO2-dataset.tsv_nif")
    return parsed_collection


def query_llm(query: str, client: InferenceClient, system_message: str = "You are an expert at entity linking."):
    user_message = query#"give me some jokes"
    prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
    
    {system_message}<|eot_id|><|start_header_id|>user<|end_header_id|>
    
    {user_message}<|eot_id|><|start_header_id|>assistant<|end_header_id|>
    """
    #More info about this function at: https://huggingface.co/docs/huggingface_hub/en/package_reference/inference_client
    answer = client.text_generation(
        prompt,
        #max_new_tokens=4096,
        do_sample=True,
        temperature=0.1,
        #repetition_penalty=1.1,
        stop= ["<|eot_id|>"]
    )
    
    
    #print("'''"+ answer +"'''")
    return answer

    if False:
        return '''{
      "examples": [
        {
          "University of Montana": "A public university in Missoula, Montana, competing in NCAA athletics.",
          "Bobby Hauck": "The head football coach at the University of Montana, known for his success in the Big Sky Conference."
        },
        {
          "Montana Tech": "A public university in Butte, Montana, known for its engineering programs and NAIA athletics.",
          "Chuck Morrell": "A former head football coach at Montana Tech who led the team in NAIA competitions."
        },
        {
          "Saint Xavier University": "A private Catholic university in Chicago, Illinois, competing in NAIA football.",
          "Mike Feminis": "The long-time head coach of Saint Xavier University's football team, leading them to an NAIA championship."
        },
        {
          "Morningside University": "A private university in Sioux City, Iowa, known for its strong NAIA football program.",
          "Steve Ryan": "The head football coach at Morningside University, leading the team to multiple NAIA championships."
        },
        {
          "Georgetown College": "A private Christian college in Kentucky, with a competitive NAIA football program.",
          "Bill Cronin": "A long-time head coach at Georgetown College, known for his success in NAIA football."
        },
        {
          "Benedictine College": "A private Catholic college in Atchison, Kansas, competing in NAIA athletics.",
          "Larry Wilcox": "The legendary head coach of Benedictine College's football team, with a career spanning decades."
        },
        {
          "Lindsey Wilson College": "A private college in Columbia, Kentucky, known for its competitive NAIA football team.",
          "Chris Oliver": "A successful head coach at Lindsey Wilson College, leading the team to an NAIA national title."
        },
        {
          "Northwestern College": "A private Christian college in Orange City, Iowa, with a strong NAIA football tradition.",
          "Matt McCarty": "The head football coach at Northwestern College, guiding the team to NAIA playoff appearances."
        },
        {
          "Grand View University": "A private university in Des Moines, Iowa, known for its successful NAIA football program.",
          "Joe Woodley": "The head coach of Grand View University's football team, continuing a strong program legacy."
        },
        {
          "Marian University": "A private Catholic university in Indianapolis, Indiana, with a highly competitive NAIA football team.",
          "Mark Henninger": "The head coach of Marian University's football team, leading them to national success in the NAIA."
        }
      ]
    }'''


def strip_thoughts(query: str):
    # Strip content within <think> and </think> tags
    # index of
    think_start = "<think>"
    think_end =   "</think>"
    start_index = query.index(think_start)
    end_index   = query.index(think_end)
    if start_index < end_index:
        beginning = query[0:start_index]
        end = query[end_index+len(think_end):len(query)]
        return beginning + end
    else:
        raise ValueError("Start index should be in front of end index: start(%s) end(%s): %s" % (start_index, end_index, query))
    return query

def get_json_from_response_file(path: str):
    with open(path, 'r', encoding='utf-8') as file:
        data = file.read()
        try:
            return json.loads(get_json_from_response(data))
        except json.JSONDecodeError as err:
            print(f"Error: Could not read JSON from [{path}]: ({data})")
            raise err
        except ValueError as err:
            print(f"Error: Could not read JSON from [{path}]: ({data})")
            raise err


def get_json_from_response(query: str):
    # Remove following
    # From start:
    #```json
    # From end:
    #```
    json_starter = "```json"
    json_ender = "```"
    query_copy = query
    start_index = query_copy.index(json_starter)
    
    query_copy = query_copy[start_index+len(json_starter) : len(query)]
    end_index   = query_copy.index(json_ender)

    if end_index > 0:
        json = query_copy[0 : end_index]
        return json
    else:
        raise ValueError("End index should be present.")
    return query


# Create prompt based on mentions
def get_plural_prompt(sentence, mentions, entities, task):
    #genprompt = GenerationPrompt(task, sentence, mentions)
    #prompt = prompt_taskdef_desc_goodmentions(genprompt)
    #prompt = prompt_taskdef_nodesc_onlygoodmentions(genprompt)
    
    #task = TaskDefinition(example=TaskExample(), steps=['read', 'new_mentions', 'create_descr', 'coherence', 'output'])
    #print(GenerationPrompt(task, "Hello world", ['world']))
    document = (sentence, mentions, entities)
    prompt = str(GenerationPrompt(task, document))
    print("Prompt:", prompt)
    return prompt


def get_singular_prompt(sentence, mention, task):
    raise ValueError("TODO: Implement singular prompt.")
    #str_mentions = ", ".join(lst_mentions[0:-1]) + f" and {lst_mentions[-1]}"
    
    singular_query = f"We are working for the entity linking task. Give 10 examples changing the mention {str_mentions} in the following sentence with other similarly fitting entity mentions. Output your reply in JSON format {{examples: [ option1: [ {{first entity mention: entity description}} ], option2: [ {{second entity mention: entity description}} ], ... ] ]}}:\n{sentence}"
    return singular_query


def query_options_llm(sentence: str, mentions: list[str], entities: list[str], client: InferenceClient, task: TaskDefinition):
    query = ""
    if len(mentions) > 1:
        query = get_plural_prompt(sentence, mentions, entities, task)
    elif len(mentions) == 1:
        query = get_singular_prompt(sentence, mentions[0], task)

    llm_query = query_llm(query, client)

    # Strip thoughts
    json_response = get_json_from_response( strip_thoughts( llm_query ) )
    print("JSON Response: ", json_response)
    json_options = None
    try:
        json_options = json.loads(json_response)
    except ValueError as err:
        print(f"Error: Could not transform to JSON ({json_response})")
        return {}

    return json_options
    

def create_dataset_options(collection: NIFCollection, result_directory: str, client: InferenceClient, task: TaskDefinition):
    # Check which ones are already done
    identifier = 0
    cache = cache_fill(result_directory)

    # Go through each document
    for context in tqdm.notebook.tqdm(collection.contexts, position=0):
        identifier += 1
        json_options = {}
        try:
            mapping_document_candidate_info = {}

            # See what can be called on context
            # print(dir(context))

            # document/context.mention = input sentence (1 document = 1 sentence)
            document = context.mention
            # If it's done already, continue to next
            if cache_check(document, cache):
                skip_counter += 1
                continue

            # Document string will be used as key for all candidate information
            key = document

            mentions = sorted(
                [(phrase.mention, phrase.beginIndex) for phrase in context.phrases],
                key=lambda x: x[1]
            )

            # Extract only the mention text after sorting
            sorted_mentions = [mention[0] for mention in mentions]

            print("Sorted Mentions:", sorted_mentions)

            entities =  [phrase.taIdentRef.replace("http://dbpedia.org/resource/", "") for phrase in context.phrases]
            json_options = query_options_llm(document, mentions, entities, client, task)

            json_options['sentence'] = document
            json_options['mentions'] = {}
            json_options['mentions']['beginIndex'] = [phrase.beginIndex for phrase in context.phrases]
            json_options['mentions']['endIndex'] = [phrase.endIndex for phrase in context.phrases]
            json_options['mentions']['mention'] = sorted_mentions
            json_options['mentions']['dbp_entity'] = [phrase.taIdentRef.replace("http://dbpedia.org/resource/", "") for phrase in context.phrases]

            with open(result_directory+"/"+str(identifier)+".json", "w") as out_file:
                json.dump(json_options, out_file, indent=4)
        except Exception as e:
            with open(result_directory+"/"+str(identifier)+"_error.json", "w") as out_file:
                json.dump(json_options, out_file, indent=4)

            print(f"Error: {e}")
            print(f"Error in document {identifier}: {document}")
            continue

        # We need the options, positions for each mention
        '''
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
        '''

def cache_fill(result_directory, mapping_path_document: dict={}, force_refill: bool=False):
    if not force_refill and mapping_path_document is not None and len(mapping_path_document) > 0:
        return mapping_path_document
        
    # to find what is where & avoid redoing
    mapping_path_document = {}
    for path in [result_directory+f for f in listdir(result_directory) if isfile(join(result_directory, f))]:
        with open(path, encoding='utf-8') as json_file:
            in_json = json.load(json_file)
        # Adapt to respective JSON structure
        lst_keys = list(dict(in_json).keys())
        if lst_keys is not None:
            key = str(lst_keys)
        else:
            key = "error"

        mapping_path_document[key] = path
    return mapping_path_document

def cache_check(document, cache):
     return document in cache.keys()

def extract_sentence_and_mentions(json_file_path):
    # Load the JSON file
    with open(json_file_path, 'r') as file:
        data = json.load(file)
    
    # Extract the sentence
    sentence = data.get("sentence", "")

    original = data.get("text", "")
    
    # Extract the mentions
    mentions = data.get("mentions", {}).get("mention", [])
    
    return sentence, original, mentions

def iterate_json_files(directory_path):
    # Generator to iterate over JSON files in the directory
    for filename in os.listdir(directory_path):
        if filename.endswith(".json"):  # Process only JSON files
            file_path = os.path.join(directory_path, filename)
            sentence, original, mentions = extract_sentence_and_mentions(file_path)
            yield {
                "file": filename,
                "original_sentence": original,
                "sentence": sentence,
                "mentions": mentions
            }

def compute_nif_hasContext(nif_data_path, search_regex="^<https://aifb\.kit\.edu/conll/.{1,4}#char=0,.{1,4}>", end_line_regex="^<https://aifb\.kit\.edu/conll/", end_line_identifier="#char=0,.{1,4}>\n"):
    docs = {}
    entities = set()
    "http://www.mpi-inf.mpg.de/yago-naga/aida/download/KORE50.tar.gz/AIDA.tsv/CEL01#char=0,18"
    with open(nif_data_path, 'r', encoding="utf-8") as f:
        for line in f:
            if re.search(search_regex, line):
                # Remove the beginning
                end_line = re.sub(end_line_regex, "", line)
                identifier = re.sub(end_line_identifier, "", end_line)

                end_char = re.sub("^<https://aifb\.kit\.edu/conll/.{1,4}#char=0,", "", line)
                end_char = re.sub(">", "", end_char)
                end_char = re.sub("\n", "", end_char)
                end_char = re.sub("\r", "", end_char)
                entry = docs.get(identifier, {})
                # If no such entry yet, add it
                if entry == {} or entry.get("end_char", None) is None:
                    entry["end_char"] = int(end_char)
                    docs[identifier] = entry
                else:
                    # it already exists, so check which one is bigger
                    prev_end_char = entry.get("end_char", 0)
                    if int(end_char) > prev_end_char:
                        entry["end_char"] = int(end_char)
                    #print("Found(%s): %d vs. %d: Winner[%d]" % (identifier, int(end_char), prev_end_char, entry["end_char"]))
        # Reconstruct lines
        for doc in docs:
            uri = "<https://aifb.kit.edu/conll/"+str(doc)+"#char=0,"+str(docs[doc]["end_char"])+">"
            entities.add(uri)
    return entities



def compute_nif_hasContextKORE50(nif_data_path):
    entities = set()
    search_regex = "^<http://www.mpi-inf.mpg.de/yago-naga/aida/download/KORE50.tar.gz/AIDA.tsv/.{5}#char=0,>"
    with open(nif_data_path, 'r', encoding="utf-8") as f:
        for line in f:
            if re.search(search_regex, line):
                entities.add(line)
    return entities

def compute_nif_hasContextACE2004t(nif_data_path):
    #
    entities = set()
    search_regex = "^<http://ace2004/dataset/.+#char=0,.{1,4}>"
    search_next_line_regex = "nif:sourceUrl <http://ace2004/dataset/"
    lines = []
    with open(nif_data_path, 'r', encoding="utf-8") as f:
        for line in f:
            if len(lines)>1 and search_next_line_regex in lines[-1]:
                # check if the previous line has the regex
                if re.search(search_regex, lines[0]):
                    entities.add(lines[0])
                else:
                    print("No match for line: ", lines[0])
            if len(lines) > 5:
                del lines[0]
            lines.append(line)
    return entities


def compute_nif_hasContextMSNBCt(nif_data_path):
    #
    entities = set()
    search_regex = "^<http://msnbc/dataset/.+#char=.{1,4},.{1,4}>"
    search_next_line_regex = "nif:sourceUrl <http://msnbc/dataset/"
    search_next_line_regex_two = "nif:broaderContext <http://msnbc/dataset/"
    lines = []
    with open(nif_data_path, 'r', encoding="utf-8") as f:
        for line in f:
            if len(lines)>1 and (search_next_line_regex in lines[-1] or search_next_line_regex_two in lines[-1]):
                # check if the previous line has the regex
                if re.search(search_regex, lines[0]):
                    entities.add(lines[0])
                else:
                    print("No match for line: ", lines[0])
            if len(lines) > 5:
                del lines[0]
            lines.append(line)
    return entities
