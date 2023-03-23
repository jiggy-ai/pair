# PAIR (Pair AI REPL)

PAIR is an AI-powered coding assistance REPL that pairs GPT-4 with you the developer to augment the best of both human and AI intelligence. It provides an interactive environment where users can input existing code, ask questions about the code or other open source projects or dependencies, receive helpful answers from the GPT-based programming assistant, add new code or refactor existing code, etc. 

The REPL supports special commands for loading files and changing directories, and it can propose code changes as context diffs that can be processed automatically. Users have the option to accept or reject the proposed changes, making PAIR a flexible and powerful tool for developers.

![Example](https://github.com/jiggy-ai/pair/blob/main/example.gif)

Currently we are using GPT-4 to help build PAIR, and are very open to other collaborators who are similarly inclined to eat their own dogfood. 

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

In the REPL, enter your questions or guidance or /file to input local files into the context.


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

The following environment variables are used to inject credentials and other required configuration for the major dependencies:

**OpenAI**

* OPENAI_API_KEY # your OpenAI API key
* PAIR_MODEL     # one of "gpt-3.5-turbo" or "gpt-4", default to gpt-4


## Community Discussions

[![](https://dcbadge.vercel.app/api/server/yNNvXuRqjH?compact=true&style=flat)](https://discord.gg/yNNvXuRqjH)

