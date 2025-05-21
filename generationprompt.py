        
from taskdefinition import TaskDefinition
import taskutils

class GenerationPrompt:
    # Static variables
    lst_positions = ['1st', '2nd', '3rd']
    lst_positions.extend([str(i)+"th" for i in range(4,20)])
    
    def __init__(self, task: TaskDefinition, document: tuple):
        self.task = task
        self.sentence = document[0]#sentence
        self.mentions = document[1]#mentions
        self.entities = document[2]#entities
    
        lst_mentions = [f'"{mention}"' for mention in self.mentions]
        self.str_mentions = taskutils.text_concatenate(lst_mentions)
        self.str_json_objects = ", ".join([f"{{{self.lst_positions[i]} mention: {self.lst_positions[i]} description}}" for i in range(0, len(lst_mentions))])
        
    def __str__(self):
        output = self.task.get_task_def_str()
        json_input = taskutils.mentiontext_to_json(text=self.sentence, mentions=self.mentions, descriptions=['...' for mention in self.mentions], entities=self.entities)
        output += '\n'
        output += '\n'.join(["**Document to process:**", json_input])
        #output += '\n'.join(["**Document:**", self.sentence, "**Mentions:**", self.str_mentions])
        #output += '\n'.join(["**Output Format:**", 
        #                     "Provide the modified text along with a list of new mentions and their descriptions in a structured format like JSON."])
        output += '\n'
        output += '\n'
        output += '\n'.join(["**Clarifications:**",
                             "- Ensure new mentions are plausible and maintain the text's meaning.",
                             "- Highlight distinguishing features in descriptions for effective disambiguation."])

        return output    