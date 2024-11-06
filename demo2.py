# Import libraries
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
import torch.nn.functional as F

from set_encoding_utils import SetEncoder

# Define model and tokenizer
model_id = "meta-llama/Meta-Llama-3-8B-instruct"
USE_SET_ENCODING = False

tokenizer = AutoTokenizer.from_pretrained(model_id)

set_encoder = SetEncoder(tokenizer)
model = AutoModelForCausalLM.from_pretrained(model_id, torch_dtype=torch.bfloat16, device_map="auto",load_in_4bit=True)

special_tokens_map = {
    "meta-llama/Llama-2-7b-chat-hf" : {"start" : "[INST]", "end" : "[/INST]"},
    "meta-llama/Meta-Llama-3-8B-instruct" : {"start" : "<|start_header_id|>user<|end_header_id|>\n\n", 
                                             "end" : "<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n"},
    "gpt2" : {"start" : "", "end" : "\n\n"},
    "mistralai/Mistral-7B-v0.3" : {"start" : "", "end" : "\n\n"},
    "meta-llama/Meta-Llama-3-8B" : {"start" : "", "end" : "\n\n"},
    "meta-llama/Llama-2-7b-hf" : {"start" : "", "end" : "\n\n"},
    "tiiuae/falcon-7b" : {"start" : "", "end" : "\n\n"},
    "mistralai/Mistral-7B-Instruct-v0.3" : {"start" : "[INST]",
                                             "end" : "[/INST]"},
    "tiiuae/falcon-7b-instruct" : {"start" : ">>QUESTION<<",
                                   "end" : ">>ANSWER<<"},
    "microsoft/Phi-3-mini-4k-instruct" : {"start" : "<|user|>\n",
                                          "end" : "<|end|>\n<|assistant|>"},                  
}

options = ["Toys", "Sweets","Tickets to Disney Land","Puppy"]

prompts = [
f"""{special_tokens_map[model_id]["start"]}What is the best present for a 5 year old?
<~start_set_marker~><~start_element_marker~>-"Toys"
<~end_element_marker~><~start_element_marker~>-"Sweets"
<~end_element_marker~><~start_element_marker~>-"Tickets to Disney Land"
<~end_element_marker~><~start_element_marker~>-"Puppy"
<~end_element_marker~><~end_set_marker~>
{special_tokens_map[model_id]["end"]}Of the presented options, the best present for a 5-year old is \"""",

f"""{special_tokens_map[model_id]["start"]}What is the best present for a 5 year old?
<~start_set_marker~><~start_element_marker~>-"Tickets to Disney Land"
<~end_element_marker~><~start_element_marker~>-"Puppy"
<~end_element_marker~><~start_element_marker~>-"Sweets"
<~end_element_marker~><~start_element_marker~>-"Toys"
<~end_element_marker~><~end_set_marker~>
{special_tokens_map[model_id]["end"]}Of the presented options, the best present for a 5-year old is \"""",

f"""{special_tokens_map[model_id]["start"]}What is the best present for a 5 year old?
<~start_set_marker~><~start_element_marker~>-"Puppy"
<~end_element_marker~><~start_element_marker~>-"Sweets"
<~end_element_marker~><~start_element_marker~>-"Toys"
<~end_element_marker~><~start_element_marker~>-"Tickets to Disney Land"
<~end_element_marker~><~end_set_marker~>
{special_tokens_map[model_id]["end"]}Of the presented options, the best present for a 5-year old is \""""]

first_tokens_of_options = []
first_ids_of_options = []
for option in options:
    option_tokens_ids = tokenizer.encode("for a 5-year old is \"" + option, add_special_tokens=False)
    option_tokens = [tokenizer.decode([x],skip_special_tokens=True) for x in option_tokens_ids]
    try:
        first_token_id = option_tokens_ids[option_tokens.index("\"") +1]
    except ValueError:
        first_token_id = option_tokens_ids[option_tokens.index(" \"") +1]
    first_ids_of_options.append(first_token_id)
    first_token = tokenizer.decode([first_token_id])
    first_tokens_of_options.append(first_token)


tokens = set_encoder(prompts, model.device)

if not USE_SET_ENCODING:
    # if set-encoding should not be used, we can simply set the "set_pos_encoding" and "set_attention-mask" to False.
    tokens["set_pos_encoding"]  = None
    tokens["set_attention_mask"] = None

with torch.no_grad():
    outputs = model(**tokens)

for prompt, output in zip(tokens["input_ids"],outputs.logits):

    print("-"*10)
    print(tokenizer.decode(prompt))
    for t, id in zip(first_tokens_of_options,first_ids_of_options):
        softmax_output =  F.softmax(output[-1], dim=0)
        print(f"The models probabability to reply with token '{t}' is {softmax_output[id]}")
    
    max_prob, max_id  = torch.max(softmax_output,dim = 0)
    if max_prob > max([softmax_output[id] for id in first_ids_of_options]):
        print(f"token with max probability is '{tokenizer.decode(max_id)}' with a probability of {max_prob}")
    
