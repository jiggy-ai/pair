import openai
import os
import sys
from chatstack import ChatContext
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion, PathCompleter, NestedCompleter, WordCompleter
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.keys import Keys

openai.api_key = os.getenv("OPENAI_API_KEY")


BASE_PROMPT = "You are a programming assistant. "
BASE_PROMPT += "The below are portions of code the user is working on as well as questions from the user. "
BASE_PROMPT += "Provide helpful answers to the user. If you need more information on code that is not included, "
BASE_PROMPT += "then ask for the definition of the code and it will be provided."


cs = ChatContext(min_response_tokens=800,  # leave room for at least this much
                 max_response_tokens=None, # don't limit the model's responses
                 max_context_assistant_messages=20,
                 max_context_user_messages=20,    
                 model="gpt-4",
                 temperature=0.1,
                 base_system_msg_text=BASE_PROMPT)
    


def repl():
    file_completer = WordCompleter(['/file'])
    path_completer = PathCompleter(only_directories=False)
    custom_completer = NestedCompleter.from_nested_dict({
        '/file': path_completer
    })

    # Create custom key bindings
    bindings = KeyBindings()

    @bindings.add(Keys.Tab)
    def _(event):
        event.app.current_buffer.complete_next()

    @bindings.add(Keys.Right)
    def _(event):
        event.app.current_buffer.complete_next()

    session = PromptSession(completer=custom_completer, key_bindings=bindings)

    while True:
        # Read user input with custom autocompletion
        user_input = session.prompt("Enter your code, questions, or /file <path>: ")

        # Check for the special /file command
        if user_input.startswith('/file'):
            file_path = user_input[6:].strip()
            try:
                with open(file_path, 'r') as file:
                    user_code =  file.read()
                    user_input = f'{file_path}:\n{user_code}\n'
                    print(f"loaded {len(user_input)} bytes from {file_path}")
            except FileNotFoundError:
                print(f"File not found: {file_path}")
                continue

        print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
        cr = cs.user_message(user_input, stream=True)
        print(f"({cr.input_tokens} + {cr.response_tokens} tokens = (${cr.price:.4f}))")
        print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")


                



if __name__ == "__main__":
    repl()

