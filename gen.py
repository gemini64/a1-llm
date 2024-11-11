import os, json
from data_model import Language, Task, generate_prompts

input_file = "./tasks.json"

# read main file
input_data = None

with open(input_file, 'r') as f_in:
    input_data = json.load(f_in)

for key in input_data.keys():
    out_file = f"{key}_prompts.json"

    prompts = []
    
    for task in input_data[key]:
        task_object = Task(**task)

        task_to_prompts = generate_prompts(task_object)
        prompts.append(task_to_prompts)

    # output all
    with open(out_file, 'w', encoding='utf8') as f_out:
        json.dump(dict(enumerate(prompts, start=1)), f_out, ensure_ascii=False)