# Generate candidates for the new mentions via DBpedia Lookup or BLINK
# Generate types for each candidate via DBpedia Lookup or SPARQL query to DBpedia endpoint
import candgenutils
import sparqlutils
# Load existing ones
base_path = "/mnt/webscistorage/wf7467/agnos/"
out_candidates_dir = base_path + "data/AIDA-YAGO2-dataset.tsv_nif_candidates/"#"C:/Users/wf7467/Desktop/GitHub/KIT/agnostic-disambiguation/data/candidates/CoNLL_AIDA-YAGO2-dataset.nif/"
out_candidates_descriptions_dir = base_path + "data/AIDA-YAGO2-dataset.tsv_nif_candidate_descriptions/"


all_candidate_results = candgenutils.load_candidate_results(result_directory=out_candidates_dir)
print(f"Loaded {len(all_candidate_results)} entries")


# For the rest: generate candidates

# save_candidate_result
# transform_dbp_json_cands_to_dict: DBpedia JSON to dict
# Step 0: Generate candidates for mentions
# Step 1: Collect all relevant URIs 
# Step 2: Query descriptions for all URIs
# Step 3: Save the results

# Step 1: For which URIs do we need additional info (aka. descriptions)?
wanted_keys = ['candidate_uris', 'true_uris']
lst_len_counter = 0
uris_for_descriptions = set()

for in_file in all_candidate_results:
    entry = all_candidate_results[in_file]
    #print(in_file, entry.keys())

    for document in entry:
        document_candidate_json = entry[document]
        for key in document_candidate_json:
            if key in wanted_keys:
                uris_of_uris = document_candidate_json[key]
                for uris in uris_of_uris:
                    lst_len_counter = lst_len_counter + len(uris)
                    uris_for_descriptions.update(uris)
                #print(len(uris_for_descriptions))
                #print(lst_len_counter)
            #break
        #break
    #break

print(lst_len_counter)
print(len(uris_for_descriptions))
print(next(iter(uris_for_descriptions)))
uris_for_descriptions = list(uris_for_descriptions)


# Step 2: Query descriptions for all URIs & save results
step = 100
file_counter_desc = 0
for i in range(0, len(uris_for_descriptions), step):
    print("Working on range[%d, %d]" % (i, i+step))
    dict_uri_desc = sparqlutils.query_descriptions_multiple_uris(uris_for_descriptions[i:i+step])
    # Step 3: Save results
    candgenutils.save_cand_desc_result(cand_desc_dictionary=dict_uri_desc, file_counter=i, result_directory=out_candidates_descriptions_dir)
    file_counter_desc += 1
