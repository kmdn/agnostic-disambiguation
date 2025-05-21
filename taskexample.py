import taskutils

class TaskExample:
    task_example_header = "Example"
    original_sentence_header = "Original"
    modified_sentence_header = "Modified"
    # Function to convert text and mentions to JSON format

    def __init__(self, original_sentence="Steve Jobs worked at Apple Inc."
                 , modified_sentence="John Smith worked at Microsoft Corporation."
                 , mentions=["Steve Jobs", "Apple Inc."]):
        self.mentions = mentions
        self.original_sentence = original_sentence
        self.modified_sentence = modified_sentence
        self.task_example_header = "Example"
        self.original_sentence_header = "Original"
        self.modified_sentence_header = "Modified"
        
    def get_example_str(self):
        str_mentions = taskutils.text_concatenate([f'"{mention}"' for mention in self.mentions])
        return '\n'.join([
                        f'**{self.task_example_header}**: ', 
                        f'- {self.original_sentence_header}: "{self.original_sentence}" with mentions {str_mentions}',
                        f'- {self.modified_sentence_header}: {self.modified_sentence}'
                         ])

    def get_example_json_str(self):
        json_original_sentence = taskutils.mentiontext_to_json("Steve Jobs worked at Apple Inc.", ['Steve Jobs', 'Apple Inc.'], ["Steven Paul Jobs (February 24, 1955 – October 5, 2011) was an American entrepreneur, industrial designer, media proprietor, and investor. He was the co-founder, chairman, and CEO of Apple.", "An American multinational technology company headquartered in Cupertino, California, United States." ])
        json_modified_sentence = taskutils.mentiontext_to_json("John Smith worked at Microsoft Corporation.", ["John Smith", "Microsoft Corporation"],
                                                     ["An entrepreneur, philosopher and experienced programmer working for Microsoft.", "A multinational technology corporation producing computer software, consumer electronics, personal computers, and related services headquartered at the Microsoft Redmond campus located in Redmond, Washington, United States. Its best-known software products are the Windows line of operating systems, the Microsoft Office suite, and the Internet Explorer and Edge web browsers."])
        return '\n'.join([
                        f'**{self.task_example_header}**: ', 
                        f'- {self.original_sentence_header}: {json_original_sentence}',
                        f'- {self.modified_sentence_header}: {json_modified_sentence}'
                         ])
        
    
    def __str__(self):
        return self.get_example_json_str()

