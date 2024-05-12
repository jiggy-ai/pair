from pydantic import BaseModel
from typing import List
from openai_models import ChatCompletionMessage, MessageContent, ImageUrl
from findfilt import find_files
from image_to_data_url import image_to_data_url
from prompt_toolkit import print_formatted_text
from prompt_toolkit.formatted_text import FormattedText
import os
from pair_context import  PairContext, FileContent



class PAIR:

    def __init__(self):
        self.project_files = []
        self.chat_messages = []
        self.project_mode = True

    def reset_files(self):
        self.project_files = []

    def disable_project_mode(self):
        self.project_files = []
        self.project_mode = False
        
    def add_file(self, filepath : str):
        print_formatted_text(FormattedText([ ("fg:violet", f'Added {filepath} to context')]))
        self.project_files.append(filepath)

    def add_user_msg(self, msg : str):
        ccmsg = ChatCompletionMessage(role    = 'user',
                                      content = msg)
        self.chat_messages.append(ccmsg)

    def add_user_image_msg(self, img_path : str):
        image_url = ImageUrl(url=image_to_data_url(img_path), detail='high')        
        ccmsg = ChatCompletionMessage(role    = 'user',
                                      content = [MessageContent(type='image_url', image_url=image_url)])
        print_formatted_text(FormattedText([ ("fg:violet", f'Added image {img_path} to context')]))        
        self.chat_messages.append(ccmsg)
        
    def add_assistant_msg(self, msg : str):
        ccmsg = ChatCompletionMessage(role    = 'assistant',
                                      content = msg)
        self.chat_messages.append(ccmsg)
        
    def remove_last_message(self):
        self.chat_messages.pop()
        
    def messages(self) -> List[ChatCompletionMessage]:
        if self.project_mode:
            file_contents = [FileContent(filename=fn, content=open(fn,'r').read()) for fn in self.project_files]
        else:
            file_contents = []

        for fc in file_contents:
            print_formatted_text(FormattedText([ ("fg:violet", f'Loaded {fc.filename} to context')]))        
    
        return PairContext(project_files = find_files(),
                           file_contents = file_contents,
                           chat_messages = self.chat_messages).messages()


