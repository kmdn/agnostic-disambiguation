# Please install OpenAI SDK first: `pip3 install openai`
from openai import OpenAI
import json, os, glob
import os.path

# Load NIF dataset
import utils
nif_data_path_lst = ["/mnt/webscistorage/wf7467/agnos/data/RSS-500.ttl", "/mnt/webscistorage/wf7467/agnos/data/AIDA-YAGO2-dataset.tsv_nif"]
nif_data_path_idx = 1
nif_data_path = nif_data_path_lst[nif_data_path_idx]
collection = utils.load_nif_dataset(nif_data_path)
print(f"Finished loading dataset[{nif_data_path}]: {collection}")

prompt_path = "/mnt/webscistorage/wf7467/agnos/prompt_generate_5_new_mention_minimized.txt"
prompt_template = ""
# Load the prompt template from a file
with open(prompt_path, "r") as f:
    prompt_template =  f.read()

# Load API key from file
api_key_file = ".deepseek_api_key.txt"
with open(api_key_file, "r") as f:
    DEEPSEEK_API_KEY = f.read().strip()

# Init LLM client
client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")


out_dir = nif_data_path_lst[nif_data_path_idx] + "_options/"
#out_dir = "/mnt/webscistorage/wf7467/agnos/data/AIDA-YAGO2-dataset.tsv_nif_options/"

# Save mappings for input document to output document(s)
out_mappings_info_dir = nif_data_path_lst[nif_data_path_idx] + "_mappings/"

# Load all mappings
mapping_keys = set()
# List all files in out_mappings_info_dir
# Get all JSON files in the directory
json_mapping_files = glob.glob(os.path.join(out_mappings_info_dir, "*.json"))
for mapping_file in json_mapping_files:
    with open(mapping_file, encoding='utf-8') as json_file:
        in_json = json.load(json_file)
        # Adapt to respective JSON structure
        mapping_keys.add(in_json.get("original_uri", ""))
        # { "original_uri": str, "response_file_path": str, "document": str}



QUERY_LLM = True

file_identifier = 0
for context in collection.contexts:

    json_options = {}
    try:
        # See what can be called on context
        # print(dir(context))
        # context_actions = [context.add_phrase, context.beginIndex, context.endIndex, context.isContextHashBasedString, context.load_from_graph, context.mention, context.original_uri, context.phrases, context.sourceUrl, context.triples, context.turtle, context.uri]
        # context_action_names = ['add_phrase', 'beginIndex', 'endIndex', 'isContextHashBasedString', 'load_from_graph', 'mention', 'original_uri', 'phrases', 'sourceUrl', 'triples', 'turtle', 'uri']
        # for action, name in zip(context_actions, context_action_names):
        #     print(f"{name}: {action}")

        # Store following info: original_uri, document, response_file_path
        # document/context.mention = input sentence (1 document = 1 sentence)
        document = context.mention
        
        # Document string will be used as key for all candidate information
        key = context.original_uri

        # If it's done already, continue to next
        # Check mappings
        if key in mapping_keys:
            print(f"Found key[{key}] Skipping...")
            continue

        sorted_mentions_entities = sorted(
            [(phrase.mention, phrase.beginIndex, phrase.endIndex, phrase.taIdentRef) for phrase in context.phrases],
            key=lambda x: x[1]
        )
        # Only take the actual mention rather than the indices for displaying
        mentions = [mention[0] for mention in sorted_mentions_entities]
        # Also have the entities sorted appropriately - otherwise the indices are faulty
        entities = [entity[3].replace("http://dbpedia.org/resource/", "").replace("http://en.wikipedia.org/wiki/", "") for entity in sorted_mentions_entities]

        # json_options = {}
        # json_options['sentence'] = document
        # json_options['mentions'] = {}
        # json_options['mentions']['beginIndex'] = [phrase.beginIndex for phrase in context.phrases]
        # json_options['mentions']['endIndex'] = [phrase.endIndex for phrase in context.phrases]
        # json_options['mentions']['uris'] = entities
        # json_options['mentions']['mention'] = mentions

        print(mentions)
        print(entities)
        print(document)

        prompt = prompt_template
        prompt += "Original Text: \""+document + "\"\n" #Officer Korey Lankow was placed on administrative leave after leaving Jeg , a drug-sniffing dog , in his squad car outside DPS headquarters in Tucson for more than an hour on July 11 ."
        prompt += "Mentions: [\"" + "\", \"".join(mentions) + "\"]" +"\n"#["Tucson", "DPS"]
        prompt += "Wikipedia IDs: [\"" + "\", \"".join(entities) + "\"]"  + "\n"#["Tucson,_Arizona", "Department_of_Public_Safety"]
        # Original Text: "Samsung released a new phone in Seoul."  
        # Mentions: ["Samsung", "Seoul"]  
        # Wikipedia IDs: ["Samsung", "Seoul"]  
        #print(prompt)

        # Response output path
        out_response_path = out_dir + str(file_identifier) + "_response.json"
        while os.path.isfile(out_response_path):
            file_identifier += 1
            out_response_path = out_dir + str(file_identifier) + "_response.json"

        # Mappings output path
        out_mappings_file = out_mappings_info_dir + str(file_identifier) + "_mappings.json"
        # Add to redundancy check for skip logic
        mapping_keys.add(key)

        # Save mappings for input document to output document(s)
        # Save the mapping information
        out_mapping_info = {}
        # Save the original URI for the document (e.g. <https://aifb.kit.edu/conll/1025#char=0,1766>)
        out_mapping_info["original_uri"] = context.original_uri
        # Save the response file path, so we know where to look for the response
        out_mapping_info["response_file_path"] = out_response_path

        # Save the input document text
        out_mapping_info["document"] = document
        # Save the original mentions
        # out_mapping_info["mentions"] = mentions
        out_mapping_info["mention_entities"] = sorted_mentions_entities
        # Save the original entities
        # out_mapping_info["entities"] = entities
        # { "original_uri": str, "response_file_path": str, "document": str}
        out_mapping_info["prompt"] = prompt

        if QUERY_LLM:
            # Use the LLM to get the new mentions
            # Dump the mapping JSON to a file for easy retrieval
            with open(out_mappings_file, "w") as out_file:
                json.dump(out_mapping_info, out_file, indent=4)
            # Open a new connection for each document

            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant, an expert at generating new mentions for entity linking tasks."},
                    {"role": "user", "content": prompt},
                ],
                stream=False,
                max_tokens=8000
            )
            # Save the response to a file
            #print(response.choices[0].message.content)
            with open(out_response_path, "w") as f:
                f.write(response.choices[0].message.content)
                print("Saved: ", out_response_path)

        #break
    except Exception as e:
        print(f"Error processing document: {e}")
        continue
    file_identifier += 1