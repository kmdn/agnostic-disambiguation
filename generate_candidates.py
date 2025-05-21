# Move this to a python script...
import candgenutils
import utils

# Generate candidates for the new mentions
base_path = "/mnt/webscistorage/wf7467/agnos/"
out_candidates_dir = base_path + "data/" + "AIDA-YAGO2-dataset.tsv_nif_candidates/"#"C:/Users/wf7467/Desktop/GitHub/KIT/agnostic-disambiguation/data/candidates/CoNLL_AIDA-YAGO2-dataset.nif/"
in_collection_path = base_path + "data/" + "generated_dataset_42.nif"#"synthetic_aida_dataset_42.nif"
#nif_dataset_output_path#
print("Loading NIF dataset from: ", in_collection_path)
syn_collection = utils.load_nif_dataset(in_collection_path)

print("Generating candidates for new mentions...")
candgenutils.compute_save_candidates_for_mentions(result_directory=out_candidates_dir, collection=syn_collection)
print("Finished generating candidates for new mentions.")