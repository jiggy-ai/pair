import openai
import os
import sys
from chatstack import ChatContext, UserMessage
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion, PathCompleter, NestedCompleter, WordCompleter
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.keys import Keys
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit import print_formatted_text
import re
import subprocess
import argparse
from .context_loader import load_files_and_urls
from .extract import url_to_text, extract_filename_code_blocks
import random
import string
import datetime
import shutil

openai.api_key = os.getenv("OPENAI_API_KEY")



BASE_PROMPT =  "You are a programming assistant. "
BASE_PROMPT += "Below are portions of code the user is working on as well as questions from the user. "
BASE_PROMPT += "Provide helpful answers to the user. If you need more information on code that is not included, "
BASE_PROMPT += "then ask for the contents of the code file or show the user how to cat the file. "
BASE_PROMPT += "When generating example code that takes an input file, have the main code take the filename as a command line argument. "
BASE_PROMPT += "When outputing code blocks, please include a filename before the code block in markdown bold like **filename.py** .  "
BASE_PROMPT += "When making changes to files, please output the entire file unless the file is very large. "
BASE_PROMPT += "If the file is too large to output in its entirety, please be sure to include 3 lines before and after each edit. "



PAIR_MODEL = os.environ.get("PAIR_MODEL", "gpt-4")
print("PAIR_MODEL =", PAIR_MODEL)

chat_ctx = ChatContext(min_response_tokens=800,  # leave room for at least this much
                       max_response_tokens=None, # don't limit the model's responses
                       chat_context_messages=20,
                       model=PAIR_MODEL,
                       temperature=0.1,
                       base_system_msg_text=BASE_PROMPT)
    
def print_help():
    print("Available commands:")
    print("/file <path> - Load a file into the context")
    print("/cd <path> - Change the current working directory")
    print("/url <url> - Load the content of a URL into the context")
    print("/status - Show the status of the OPENAI_API_KEY and the model being used")
    print("/help - Display this help message")
    

parser = argparse.ArgumentParser(description="Load files and URLs into the context")
parser.add_argument("items", nargs="*", help="List of files and URLs to load into the context")
args = parser.parse_args()
load_files_and_urls(chat_ctx, args.items)








def repl():
    path_completer = PathCompleter(only_directories=False, expanduser=True)
    custom_completer = NestedCompleter.from_nested_dict({
        '/file': path_completer,
        '/cd': path_completer,
        '/url': WordCompleter(['http://', 'https://']),
    })

    # Create custom key bindings
    bindings = KeyBindings()

    @bindings.add(Keys.Tab)
    def _(event):
        b = event.app.current_buffer
        if b.complete_state:
            b.complete_next()
        else:
            b.start_completion(select_first=True)


    @bindings.add(Keys.Right)
    def _(event):
        event.app.current_buffer.complete_next()

    session = PromptSession(completer=custom_completer, key_bindings=bindings)
    print_formatted_text(FormattedText([("fg:violet", "Pair AI Programming REPL  ")]))
    while True:
        # Read user input with custom autocompletion
        user_input = session.prompt("Enter your code, questions, or /file <path>,  or /help to see all commands:  \n")

        if user_input.strip() == '':
            continue

        # Check for the special /file command
        if user_input.startswith('/file'):
            file_path = user_input[6:].strip()
            try:
                with open(file_path, 'r') as file:
                    user_code =  file.read()
                    user_input = f'{file_path}:\n{user_code}\n'
                    msg = UserMessage(text=user_input)
                    chat_ctx.add_message(msg)
                    print(f"Loaded {file_path} into context ({msg.tokens} tokens)")
                    continue
            except FileNotFoundError:
                print(f"File not found: {file_path}")
                continue
            except IsADirectoryError:
                print(f"Path is a directory, not a file: {file_path}")
                continue
            except Exception as e:
                print(f"Unexpected error: {e}")
                continue
        # Check for the special /cd command
        elif user_input.startswith('/cd'):
            dir_path = user_input[4:].strip()
            try:
                os.chdir(os.path.expanduser(dir_path))
                print(f"Changed directory to: {os.getcwd()}")
            except FileNotFoundError:
                print(f"Directory not found: {dir_path}")
                continue
            except NotADirectoryError:
                print(f"Not a directory: {dir_path}")
                continue
            continue  # Add this line to skip processing the /cd command as a user input for assistance         
        # Check for the special /url command
        elif user_input.startswith('/url'):
             url = user_input[5:].strip()
             try:
                 content, title, language = url_to_text(url)
                 user_input = f'{url}:\n{content}\n'
                 msg = UserMessage(text=user_input)
                 chat_ctx.add_message(msg)
                 print(content)
                 print(f"Loaded {url} into context ({msg.tokens} tokens)")
                 continue
             except Exception as e:
                 print(f"Error fetching URL: {e}")
                 continue
        # Check for the special /status command
        elif user_input.startswith('/status'):
            api_key_status = "set" if openai.api_key else "not set"
            model_name = chat_ctx.model
            try:
                openai.Model.retrieve(model_name)
                model_status = "available"
            except Exception as e:
                model_status = f"unavailable ({e})"

            print(f"OPENAI_API_KEY: {api_key_status}")
            print(f"Model: {model_name} ({model_status})")
            continue  # Add this line to skip processing the /status command as a user input for assistance
        # Check for the special /help command
        elif user_input.startswith('/help'):
            print_help()
            continue  # Add this line to skip processing the /help command as a user input for assistance            
        
        print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  ")
        for cr in chat_ctx.user_message_stream(user_input):
            sys.stdout.write(cr.delta)
            sys.stdout.flush()
        
        print_formatted_text(FormattedText([("fg:olive", f"\n({cr.input_tokens} + {cr.response_tokens} tokens = ${cr.price:.4f})  ")]))
        print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  ")

        # extract code blocks from completion text along with filename
        filename_code_blocks = extract_filename_code_blocks(cr.text)
        skipped = 0
        for filename, codeblock, filetype in filename_code_blocks:
            if filename is None:
                ## consider saving unnamed code snippets
                skipped += 1
                continue
            
            if os.path.exists(filename):
                if os.path.getsize(filename) > len(codeblock):
                    # new content is smaller than old content, so don't overwrite
                    filename += ".edit"
                else:
                    # will overwrite
                    # create backup of original file
                    dtstr = datetime.datetime.now().strftime("%Y%m%d_%H%MS")
                    shutil.copy2(filename, filename + f'.pair-{dtstr}')

            if '/' in filename:
                # brutally create directories that dont already exist
                os.makedirs("/".join(filename.split('/')[:-1]), exist_ok=True)
            try:
                with open(filename, 'w') as fp:
                    fp.write(codeblock)
                    print_formatted_text(FormattedText([ ("fg:violet", "extracted "), ("fg:chocolate", filetype), 
                                                         ("fg:violet", " block as "), ("fg:chocolate", filename) ]))
            except Exception as e:
                print_formatted_text(FormattedText([ ("fg:violet", "error extracting filename")]))
        if skipped:
            print_formatted_text(FormattedText([ ("fg:violet", f"skipped unnamed code snippet{'s' if skipped > 1 else ''}")]))
                
                



if __name__ == "__main__":
    repl()

