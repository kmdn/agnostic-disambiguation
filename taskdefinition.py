from taskexample import TaskExample

class TaskDefinition:

    # Task-related textual semi-constants
    task_explanation_header = "Task Explanation"
    task_explanation = "You are tasked with modifying an existing entity linking dataset to prevent contamination in evaluations. Replace each entity mention with a new, semantically similar but distinct entity, while preserving context and coherence."
    # Step related semi-constants
    step_read = "Extract the given text containing entity mentions."
    step_new_mentions = "Replace each existing mention with a new one of the same type and domain."
    step_create_descriptions = "For each new mention, produce a brief, descriptive phrase highlighting distinguishing features."
    step_mention_coherence = "Modify the text to integrate the new mentions naturally."
    step_output_format = "Structure the output in an easily-processable JSON format."
    # Maps action to position in lists (for headers and actual text content) for adaptive/easy lookup
    dict_possible_steps = {'read': 0, 'new_mentions': 1, 'create_descr': 2, 'coherence': 3, 'output': 4}
    steps_headers = ["Read Text", "Generate New Mentions", "Create Descriptions", "Ensure Coherence", "Prepare Output"]
    # Repository for possible texts for each step
    lst_possible_steps_str = [step_read, step_new_mentions, step_create_descriptions, step_mention_coherence, step_output_format]
    # Part of task definition where we tell the LLM what to do
    steps_to_do_header = "Steps to Follow"
    # Default steps
    wanted_steps = ['read', 'new_mentions', 'create_descr', 'coherence', 'output']

    def __init__(self, example: TaskExample, steps=['read', 'new_mentions', 'create_descr', 'coherence', 'output']):
        self.wanted_steps = steps
        self.example = example
        
    def __str__(self):
        return self.get_task_def_str(self)
    
    def get_possible_steps(self):
        global wanted_steps
        return self.dict_possible_steps.keys()

    def get_steps(self):
        return self.wanted_steps

    def get_steps_str(self):
        # Concatenates all the wanted steps in order of appearance in "wanted_steps"
        output = '\n'.join([f'{i+1}. **{self.steps_headers[self.dict_possible_steps[step]]}:** {self.lst_possible_steps_str[self.dict_possible_steps[step]]}' for i, step in enumerate(self.wanted_steps)])
        return output

    def get_task_def_str(self):
        # Explanation
        output = f'**{self.task_explanation_header}**:\n{self.task_explanation}\n\n'
        # Steps
        output += f'**{self.steps_to_do_header}**:\n{self.get_steps_str()}\n'
        # Examples?
        output += f'\n{str(self.example)}\n'
        return output
