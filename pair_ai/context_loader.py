import os
import re
from .extract import url_to_text
from chatstack import UserMessage

def is_url(string):
    url_pattern = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
    return bool(url_pattern.match(string))

def load_files_and_urls(chat_ctx, items):
    for item in items:
        if is_url(item):
            try:
                content, title, language = url_to_text(item)
                user_input = f'{item}:\n{content}\n'
                msg = UserMessage(text=user_input)
                chat_ctx.add_message(msg)
                print(f"Loaded {msg.tokens} tokens from {item} into context")
            except Exception as e:
                print(f"Error fetching URL: {e}")
        else:
            try:
                with open(item, 'r') as file:
                    user_code = file.read()
                    user_input = f'{item}:\n{user_code}\n'
                    msg = UserMessage(text=user_input)
                    chat_ctx.add_message(msg)
                    print(f"Loaded {msg.tokens} tokens from {item} into context")
            except FileNotFoundError:
                print(f"File not found: {item}")
            except IsADirectoryError:
                print(f"Path is a directory, not a file: {item}")
            except Exception as e:
                print(f"Unexpected error: {e}")
