Pair AI Programming REPL  
Enter your code, questions, or /file <path>, or /cd <path>:  
**/file pair.py**  
loaded 763 tokens from pair.py into context  

Enter your code, questions, or /file <path>, or /cd <path>:

**lets modify this to take multiline input that submits with control-d**
    
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
To modify the code to accept multiline input and submit with Control-D, you can update the `repl()` function as follows:

1. Replace the `PromptSession` initialization with a multiline configuration and a custom key binding for Control-D.
2. Update the `user_input` prompt to handle multiline input.

Here's the updated `repl()` function:

```python
def repl():
    path_completer = PathCompleter(only_directories=False)
    custom_completer = NestedCompleter.from_nested_dict({
        '/file': path_completer,
        '/cd': path_completer
    })

    # Create custom key bindings
    bindings = KeyBindings()

    @bindings.add(Keys.Tab)
    def _(event):
        event.app.current_buffer.complete_next()

    @bindings.add(Keys.Right)
    def _(event):
        event.app.current_buffer.complete_next()

    @bindings.add(Keys.ControlD)
    def _(event):
        event.app.exit()

    session = PromptSession(completer=custom_completer, key_bindings=bindings, multiline=True)
    print("Pair AI Programming REPL")
    while True:
        # Read user input with custom autocompletion
        user_input = session.prompt("Enter your code, questions, or /file <path>, or /cd <path>:\n", key_bindings=bindings)

        # Check for the special /file command
        if user_input.startswith('/file'):
            file_path = user_input[6:].strip()
            try:
                with open(file_path, 'r') as file:
                    user_code =  file.read()
                    user_input = f'{file_path}:\n{user_code}\n'
                    msg = UserMessage(text=user_input)
                    chat_ctx.add_message(msg)
                    print(f"loaded {msg.tokens} tokens from {file_path} into context")
                    continue
            except FileNotFoundError:
                print(f"File not found: {file_path}")
                continue
        # Check for the special /cd command
        elif user_input.startswith('/cd'):
            dir_path = user_input[4:].strip()
            try:
                os.chdir(dir_path)
                print(f"Changed directory to: {os.getcwd()}")
            except FileNotFoundError:
                print(f"Directory not found: {dir_path}")
                continue
            except NotADirectoryError:
                print(f"Not a directory: {dir_path}")
                continue
            continue  # Add this line to skip processing the /cd command as a user input for assistance
            
        print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
        cr = chat_ctx.user_message(user_input, stream=True)
        print_formatted_text(FormattedText([("fg:olive", f"({cr.input_tokens} + {cr.response_tokens} tokens = ${cr.price:.4f})")]))
        print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
```

Now, the REPL will accept multiline input and submit it when you press Control-D.
    
(847 + 602 tokens = $0.0615)

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~    
Enter your code, questions, or /file <path>, or /cd <path>:    
**can you just output the diff?**  
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~   
Certainly! Here's the diff for the changes in the `repl()` function:

```diff
  def repl():
      ...
      # Create custom key bindings
      bindings = KeyBindings()
  
      ...
  
+     @bindings.add(Keys.ControlD)
+     def _(event):
+         event.app.exit()
+ 
-     session = PromptSession(completer=custom_completer, key_bindings=bindings)
+     session = PromptSession(completer=custom_completer, key_bindings=bindings, multiline=True)
      print("Pair AI Programming REPL")
      while True:
          # Read user input with custom autocompletion
-         user_input = session.prompt("Enter your code, questions, or /file <path>, or /cd <path>:\n")
+         user_input = session.prompt("Enter your code, questions, or /file <path>, or /cd <path>:\n", key_bindings=bindings)
  
          ...
```
    
These changes add a new key binding for Control-D to exit the input, set the `multiline` parameter to `True` in the `PromptSession` initialization, and pass the `key_bindings` to the `session.prompt()` method.
    
(1462 + 254 tokens = $0.0591)

These changes add a new key binding for Control-D to exit the input, set the `multiline` parameter to `True` in the `PromptSession` initialization, and pass the `key_bindings` to the `session.prompt()` method.
(1462 + 254 tokens = $0.0591)
