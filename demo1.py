
# Import libraries
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

from set_encoding_utils import SetEncoder

model_id = "meta-llama/Meta-Llama-3-8B-instruct"
USE_SET_ENCODING = True


# Models with set-encoding enabled are:
VALID_MODELS = ["mistralai/Mistral-7B-Instruct-v0.3",
    "mistralai/Mistral-7B-v0.3",
    "microsoft/Phi-3-mini-4k-instruct",
    "meta-llama/Meta-Llama-3-8B",
    "meta-llama/Llama-2-7b-hf",
    "tiiuae/falcon-7b",
    "gpt2",
    "meta-llama/Meta-Llama-3-8B-instruct",
    "meta-llama/Llama-2-7b-chat-hf",
    "tiiuae/falcon-7b-instruct"]

assert model_id in VALID_MODELS



tokenizer = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForCausalLM.from_pretrained(model_id, torch_dtype=torch.bfloat16, device_map="auto",load_in_4bit=True)
set_encoder = SetEncoder(tokenizer)

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

order = ["Potato","Tomato","Apple"]

prompts = [
f"""{special_tokens_map[model_id]["start"]}Here is a list:
<~start_set_marker~><~start_element_marker~>-Melon
<~end_element_marker~><~start_element_marker~>-Apple
<~end_element_marker~><~start_element_marker~>-Banana
<~end_element_marker~><~end_set_marker~>
What is the first item in the list?{special_tokens_map[model_id]["end"]}""",

f"""{special_tokens_map[model_id]["start"]}Here is a list
<~start_set_marker~><~start_element_marker~>-Melon
<~end_element_marker~><~start_element_marker~>-Apple
<~end_element_marker~><~start_element_marker~>-Banana
<~end_element_marker~><~end_set_marker~>
What is the second item in the list?{special_tokens_map[model_id]["end"]}""",

f"""{special_tokens_map[model_id]["start"]}Here are some facts:
<~start_set_marker~><~start_element_marker~>-Karl feeds the pigeons, whenever he is in the park.
<~end_element_marker~><~start_element_marker~>-Kall goes to the park on sunny days.
<~end_element_marker~><~start_element_marker~>-Today it is sunny.
<~end_element_marker~><~end_set_marker~>
Given these facts. Is someone feeding the pigeons today?{special_tokens_map[model_id]["end"]}"""]

# Tokenize the prompts
tokens = set_encoder(prompts, model.device)

if not USE_SET_ENCODING:
    # if set-encoding should not be used, we can simply set the "set_pos_encoding" and "set_attention-mask" to False.
    tokens["set_pos_encoding"]  = None
    tokens["set_attention_mask"] = None

model = AutoModelForCausalLM.from_pretrained(model_id, torch_dtype=torch.bfloat16, device_map="auto")

torch.manual_seed(42)
with torch.no_grad():
    outputs = model.generate(
        **tokens,
        max_new_tokens=500
    )

# Decode the generated tokens
answers = [tokenizer.decode(output,skip_special_tokens=True) for output in outputs]

# Print the answers
for i, answer in enumerate(answers):
    print("\n---------------------\n")
    print(f"'{answer}'\n")

