

from pydantic import BaseModel, Field
from openai_models import ChatCompletionMessage
from typing import List
import mimetypes

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
        BASE_PROMPT += "When making edits to existing files, output a context diff of the changes."
        BASE_PROMPT += "Don't make assumptions about the contents of a file. If you need to see the contents of a file to perform a task, use a code block with contents 'cat filename'. "
        
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
        return messages + self.chat_messages


        
class FilesContext(BaseModel):
    project_files : str      # list of filenames in the project directory
    chat_messages : List[ChatCompletionMessage]

    def messages(self) -> List[ChatCompletionMessage]:

        BASE_PROMPT =  "You are a programming assistant. "
         
        messages  = [ChatCompletionMessage(role='system', content=BASE_PROMPT)]

        # introduce the project files
        filesprompt = "Here is a listing all files in our project directory: \n"
        filesprompt += self.project_files
        
        messages  += [ChatCompletionMessage(role='system', content=filesprompt)]

        query = "Which of the existing files do we need to read, reference, or edit for this task?"
        messages  += [ChatCompletionMessage(role='system', content=query)]
        
        # add the chat messages to the end
        return messages + self.chat_messages[-3:]





class FileList(BaseModel):
    filenames: List[str] = Field(description = 'A filename that needs to be read or edited in order to respond to the user.')
