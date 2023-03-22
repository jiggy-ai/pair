# PAIR (Pair AI REPL)

PAIR is an AI-powered pair programming REPL that leverages GPT-4 to assist developers in writing and understanding code. It provides a seamless interactive environment where users can input code, ask questions, and receive helpful answers from the GPT-based programming assistant. The REPL supports special commands for loading files and changing directories, and it can propose code changes as context diffs that can be processed automatically. Users have the option to accept or reject the proposed changes, making PAIR a flexible and powerful tool for developers.

![Example](https://github.com/jiggy-ai/pair/blob/main/example.gif)

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


When PAIR detects a diff in the model output, it extracts the diff and presents it to the user.  If the user accepts the diff then the diff is applied to the referenced source file using patch.  There are probably a lot of corner cases here so I expect this functionality to be fragile.

See [example.md](https://github.com/jiggy-ai/pair/blob/main/example.md) for a typical edit interaction.


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

