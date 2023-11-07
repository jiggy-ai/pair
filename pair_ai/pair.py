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
from .extract import url_to_text

openai.api_key = os.getenv("OPENAI_API_KEY")



BASE_PROMPT = "You are a programming assistant. "
BASE_PROMPT += "The below are portions of code the user is working on as well as questions from the user. "
BASE_PROMPT += "Provide helpful answers to the user. If you need more information on code that is not included, "
BASE_PROMPT += "then ask for the definition of the code and it will be provided.  "



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
        # check response text for a diff 
        diff_match = re.search(r'```diff(.*?)```', cr.text, re.DOTALL)
        if diff_match:
            diff = diff_match.group(1).strip()
            print_formatted_text(FormattedText([("fg:violet", "Found diff in model output:\n")]))
            print_formatted_text(FormattedText([("fg:darkred", diff)]))

            # Ask the user if they accept the diff
            accept_diff = input("Do you accept the diff? (yes/no): ").lower()
            if accept_diff == 'yes':
                try:
                    with open("temp_diff.patch", "w") as temp_diff_file:
                        temp_diff_file.write(diff)

                    subprocess.run(["patch", "-p1", "-i", "temp_diff.patch"], check=True)
                    os.remove("temp_diff.patch")

                    print("Diff applied successfully.")
                except Exception as e:
                    print(f"Error applying diff: {e}")
            else:
                print_formatted_text(FormattedText([("fg:red", "Diff not applied.")]))
        else:
            print_formatted_text(FormattedText([("fg:red", "No diff found in the response.")]))

                



if __name__ == "__main__":
    repl()

