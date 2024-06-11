import subprocess

def apply_patch(filepath):
    """
    Apply a patch from a .diff file.

    :param filepath: Path to the .diff file
    :raises RuntimeError: If the patch command fails
    """
    try:
        # Run the patch command
        result = subprocess.run(['patch', '-i', filepath], check=True, capture_output=True, text=True)
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        # Raise an exception if the patch command fails
        raise RuntimeError(f"Failed to apply patch: {e.stderr}")

# Example usage
if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python apply_patch.py <path_to_diff_file>")
        sys.exit(1)
    
    diff_file_path = sys.argv[1]
    try:
        apply_patch(diff_file_path)
        print("Patch applied successfully.")
    except RuntimeError as e:
        print(e)
