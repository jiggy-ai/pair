import openai
import os
import sys
from rich.console import Console
from rich.markdown import Markdown
from chatstack import ChatContext

openai.api_key = os.getenv("OPENAI_API_KEY")


BASE_PROMPT = "You are a programming assistant. "
BASE_PROMPT += "The below are portions of code the user is working on as well as questions from the user. "
BASE_PROMPT += "Provide helpful answers to the user. If you need more information on code that is not included, "
BASE_PROMPT += "then ask for the definition of the code and it will be provided."


cs = ChatContext(min_response_tokens=800,  # leave room for at least this much
                 max_response_tokens=None, # don't limit the model's responses
                 max_context_assistant_messages=5,
                 max_context_user_messages=50,    
                 model="gpt-4",
                 temperature=0.1,
                 base_system_msg_text=BASE_PROMPT)
    


def repl():
    while True:
        # read from standard input until EOF
        print("Enter your code and questions.  Press Ctrl+D to end input:")
        user_input = sys.stdin.read()
        print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
        response = cs.user_message(user_input, stream=True)
        print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
    
