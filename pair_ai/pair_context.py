

from pydantic import BaseModel
from openai_models import ChatCompletionMessage


class FileContent(BaseModel):
    filename:  str
    content:   str

    def messages(self) -> List[ChatCompletionMessage]:
        content = f"filename: {self.filename}\n{self.content}"
        return [ChatCompletionMessage(role='system', content=content)]


    
class PairContext(BaseModel):

    project_files : str                             # list of filenames in the project directory
    file_contents : List[FileContent]    
    chat_messages : List[ChatCompletionMessage]


    def messages(self) -> List[ChatCompletionMessage]:

        BASE_PROMPT =  "You are a programming assistant. "
        BASE_PROMPT += "Below are portions of code the user is working on as well as questions from the user. "
        BASE_PROMPT += "Provide helpful answers to the user. If you need more information on code that is not included, "
        BASE_PROMPT += "ask for the contents of the code file or show the user how to cat the file in question. "
        BASE_PROMPT += "When generating example code that takes an input file, arrange the main code to take the filename as a command line argument. "
        BASE_PROMPT += "When outputing code blocks, please include a filename before the code block in markdown bold like **filename.py** .  "
        BASE_PROMPT += "When making edits to existing files, please output the entire file unless the file is very large. "
        BASE_PROMPT += "If the file is too large to output in its entirety, please be sure to include 3 lines before and after each edit. "

        messages  = [ChatCompletionMessage(role='system', content=BASE_PROMPT)]

        # introduce the project files
        filesprompt = "Here is a listing all files in our project directory: \n"
        filesprompt += self.project_files
        
        messages  += [ChatCompletionMessage(role='system', content=filesprompt)]

        # introduce the file contents
        file_intro = "Here are file contents that might be helpful for completing the task. "
        file_intro += "Please ask if you need to see the contents of any of the other files. "

        # add the file contents
        messages  += [ChatCompletionMessage(role='system', content=file_intro)]
        for f in self.file_contents:
            messages += f.messages()

        # add the chat messages to the end
        return messages + self.chat_messages[:10]  

        
