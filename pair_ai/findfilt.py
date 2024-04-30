import os
import fnmatch

def find_gitignore(start_path):
    """ Search for .gitignore file starting from the given directory upwards to the root directory. """
    current_path = start_path
    while os.path.dirname(current_path) != current_path:  # check if we've reached the root
        gitignore_path = os.path.join(current_path, '.gitignore')
        if os.path.exists(gitignore_path):
            return gitignore_path
        current_path = os.path.dirname(current_path)
    return None

def parse_gitignore(gitignore_path):
    """ Parse the .gitignore file to extract patterns. """
    patterns = []
    with open(gitignore_path, 'r') as file:
        for line in file:
            stripped = line.strip()
            if stripped and not stripped.startswith('#'):
                patterns.append(stripped)
    return patterns

def match_patterns(path, patterns):
    """ Check if the path matches any of the patterns. """
    for pattern in patterns:
        if fnmatch.fnmatch(path, pattern):
            return True
    return False

def find_files_filtered(base_path, ignored_patterns):
    """ Recursively yield file paths that are not ignored by the .gitignore patterns. """
    for root, dirs, files in os.walk(base_path, topdown=True):
        # Modify dirs in-place for os.walk to correctly ignore directories
        dirs[:] = [d for d in dirs if not match_patterns(d, ignored_patterns)]

        for file in files:
            file_path = os.path.join(root, file)
            if not match_patterns(file, ignored_patterns):
                yield file_path

def find_files() -> str:
    """
    return listing of files like find under the current directory
    """
    start_dir = os.getcwd()
    gitignore_path = find_gitignore(start_dir)

    ignored_patterns = [".git*"]

    filelist = ""
    if gitignore_path:
        ignored_patterns.extend(parse_gitignore(gitignore_path))


    for file_path in find_files_filtered(start_dir, ignored_patterns):
        relative_path = os.path.relpath(file_path, start=start_dir)
        if not relative_path.startswith('.'):
            relative_path = f"./{relative_path}"
        filelist += relative_path + "\n"
    return filelist
