# PAIR (Pair AI REPL)

PAIR is a GPT-based pair programming REPL that assists coders and GPTs in dealing with code. 

Currently I am using GPT-4 to help build PAIR, and am open to other collaborators. 

## Installation

To install Pair AI, run the following command:

```bash
pip install pair_ai
```

## Usage

After installing the package, you can use the `pair` command in your terminal or command prompt to start the REPL:

```bash
pair
```

In the REPL, enter your code and questions, then press `Ctrl+D` to end input and receive a response from the GPT-based programming assistant.


### Commands

- `/file <path>`: Load a file's content into the model context by providing its path.
- `/cd <path>`: Change the current working directory to the specified path.

To use the special commands, simply type the command followed by the appropriate path or command in the REPL.

Example:

```
/file /path/to/your/file.py
/cd /path/to/your/directory
```
## Dependencies

- [chatstack](https://github.com/jiggy-ai/chatstack)
- prompt_toolkit

```
