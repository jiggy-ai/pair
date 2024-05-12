#!/usr/bin/env python

import os
import sys
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion, PathCompleter, NestedCompleter, WordCompleter
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.keys import Keys
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit import print_formatted_text
from extract import url_to_text, extract_filename_code_blocks
import datetime
import shutil
from pair_state import PAIR
from gpt_wrapper import completions, extract_dataclass
import mimetypes
from pair_context import  FilesContext, FileList
from findfilt import find_files

PAIR_MODEL = os.environ.get("PAIR_MODEL", "gpt-4")
print("PAIR_MODEL =", PAIR_MODEL)


    
def print_help():
    print("Available commands:")
    print("/file <path> - Load a file into the context")
    print("/url <url> - Load the content of a URL into the context")
    print("/help - Display this help message")
    


pair_state = PAIR()


for arg in sys.argv[1:]:
    if arg == "-p":
        pair_state.disable_project_mode()
        print("Disabling project mode: local file listing will not be loaded into model context & output files will not be saved to disk")
        continue
    if os.path.isfile(arg):
        fn = arg
        if mimetypes.guess_type(fn)[0] in ["image/png", "image/jpeg"]:
            pair_state.add_user_image_msg(fn)
        else:
            pair_state.add_file(fn)
            

            
def save_code_blocks(code_blocks):
    """
    save code blocks to files
    """
    skipped = 0
    for cb in code_blocks:
        if cb.filename is None:
            ## consider saving unnamed code snippets
            skipped += 1
            continue
        
        if os.path.exists(cb.filename):
            if os.path.getsize(cb.filename) > len(cb.code):
                # new content is smaller than old content, so don't overwrite
                cb.filename += ".edit"
            else:
                # will overwrite
                # create backup of original file
                dtstr = datetime.datetime.now().strftime("%Y%m%d_%H%MS")
                shutil.copy2(cb.filename, cb.filename + f'.pair-{dtstr}')

        if '/' in cb.filename:
            # brutally create directories that dont already exist
            os.makedirs("/".join(cb.filename.split('/')[:-1]), exist_ok=True)
        try:
            with open(cb.filename, 'w') as fp:
                fp.write(cb.code)
                print_formatted_text(FormattedText([ ("fg:violet", "extracted "), ("fg:chocolate", cb.type), 
                                                    ("fg:violet", " block as "), ("fg:chocolate", cb.filename) ]))
        except Exception as e:
            print_formatted_text(FormattedText([ ("fg:violet", "error extracting filename")]))
    if skipped:
        print_formatted_text(FormattedText([ ("fg:violet", f"skipped unnamed code snippet{'s' if skipped > 1 else ''}")]))



def validate_filelist(filelist, content):
    for fn in filelist.filenames:
        if not os.path.exists(fn):
            raise ValueError(f"File {fn} not found")
    
def repl():
    path_completer = PathCompleter(only_directories=False, expanduser=True)
    custom_completer = NestedCompleter.from_nested_dict({
        '/file': path_completer,
        '/clear_files': None,
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
                pair_state.add_file(file_path)
            except FileNotFoundError:
                print(f"File not found: {file_path}")
                continue
            except IsADirectoryError:
                print(f"Path is a directory, not a file: {file_path}")
                continue
            except Exception as e:
                print(f"Unexpected error: {e}")
                continue
        elif user_input.startswith('/clear_files'):
            pair_state.reset_files()
            print_formatted_text(FormattedText([("fg:violet", "Cleared files from context")]))
            continue
        # Check for the special /url command
        elif user_input.startswith('/url'):
             url = user_input[5:].strip()
             try:
                 content, title, language = url_to_text(url)
                 user_input = f'{url}:\n{content}\n'
                 pair_state.add_user_msg(user_input)
                 print(user_input)
                 continue
             except Exception as e:
                 print(f"Error fetching URL: {e}")
                 continue
    
        # Check for the special /help command
        elif user_input.startswith('/help'):
            print_help()
            continue  # Add this line to skip processing the /help command as a user input for assistance            

        pair_state.add_user_msg(user_input)

        if pair_state.project_mode:
            # get set of files we need to complete the task
            filelist = extract_dataclass(FilesContext(project_files = find_files(), 
                                                    chat_messages = pair_state.chat_messages).messages(),
                                         FileList,
                                         task_validator=validate_filelist)
            for fn in filelist.filenames:
                pair_state.add_file(fn)
                                    
        
        print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  ")
        try:
            for cr in completions(messages=pair_state.messages(), model=PAIR_MODEL):
                sys.stdout.write(cr.delta)
                sys.stdout.flush()
        except KeyboardInterrupt:
            pair_state.remove_last_message()
            print_formatted_text(FormattedText([("fg:violet", "\n\nInterrupted; your last message and model response were not added to conversation state...")]))
            continue
        pair_state.add_assistant_msg(cr.text)
        
        print_formatted_text(FormattedText([("fg:olive", f"\n({cr.input_tokens} + {cr.response_tokens} tokens = ${cr.price:.4f})  ")]))
        print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  ")

        # extract code blocks from completion text along with filename
        if pair_state.project_mode:
            # extract code blocks from completion text along with filename
            code_blocks = extract_filename_code_blocks(cr.text)            
            save_code_blocks(code_blocks)
            # add files to project state
            for cb in code_blocks:
                if cb.filename:
                    pair_state.add_file(cb.filename)
                
        


if __name__ == "__main__":
    repl()

