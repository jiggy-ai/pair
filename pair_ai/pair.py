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

openai.api_key = os.getenv("OPENAI_API_KEY")


BASE_PROMPT = "You are a programming assistant. "
BASE_PROMPT += "The below are portions of code the user is working on as well as questions from the user. "
BASE_PROMPT += "Provide helpful answers to the user. If you need more information on code that is not included, "
BASE_PROMPT += "then ask for the definition of the code and it will be provided.  "
BASE_PROMPT += "When making code changes output them as diff compatible output that can be processed with patch command "
BASE_PROMPT += "(including filename and line numbers) unless the user asks for a full file or a function."



chat_ctx = ChatContext(min_response_tokens=800,  # leave room for at least this much
                       max_response_tokens=None, # don't limit the model's responses
                       max_context_assistant_messages=20,
                       max_context_user_messages=20,    
                       model=os.environ.get("PAIR_MODEL", "gpt-4"),
                       temperature=0.1,
                       base_system_msg_text=BASE_PROMPT)
    


def repl():
    path_completer = PathCompleter(only_directories=False, expanduser=True)
    custom_completer = NestedCompleter.from_nested_dict({
        '/file': path_completer,
        '/cd': path_completer
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
        user_input = session.prompt("Enter your code, questions, or /file <path>, or /cd <path>:  \n")

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
                    print(f"Loaded {msg.tokens} tokens from {file_path} into context  ")
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
            
        print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  ")
        cr = chat_ctx.user_message(user_input, stream=True)
        print_formatted_text(FormattedText([("fg:olive", f"({cr.input_tokens} + {cr.response_tokens} tokens = ${cr.price:.4f})  ")]))
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

