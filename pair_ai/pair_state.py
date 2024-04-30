


from pydantic import BaseModel
from typing import List
from openai_models import ChatCompletionMessage
from findfilt import find_files

from pair_context import  PairContext, FileContent




class PAIR:

    def __init__(self):
        self.project_files = []
        self.chat_messages = []

    def add_file(self, filepath : str):
        print(f'add {filepath} to context')
        self.project_files.append(filepath)

    def add_user_msg(self, msg : str):
        ccmsg = ChatCompletionMessage(role    = 'user',
                                      content = msg)
        self.chat_messages.append(ccmsg)

        
    def add_assistant_msg(self, msg : str):
        ccmsg = ChatCompletionMessage(role    = 'assistant',
                                      content = msg)
        self.chat_messages.append(ccmsg)
        
        
    def messages(self) -> List[ChatCompletionMessage]:

        file_contents = [FileContent(filename=fn, content=open(fn,'r').read()) for fn in self.project_files]

        for fc in file_contents:
            print(f'loaded {fc.filename} in context')

        return PairContext(project_files = find_files(),
                           file_contents = file_contents,
                           chat_messages = self.chat_messages).messages()

