import os
import sys

# Ensure output is in ASCII to avoid encoding issues
sys.stdout.reconfigure(encoding="ascii", errors="replace")

def generate_tree(directory, prefix="", folders_only=False, exclude_dirs=None):
    """Recursively generates an ASCII directory tree."""
    if exclude_dirs is None:
        exclude_dirs = {"venv", "env", "__pycache__"}  # Common virtual environments and cache folders
    
    entries = sorted(os.listdir(directory))
    entries = [e for e in entries if not e.startswith(".")]  # Exclude hidden files
    
    if folders_only:
        entries = [e for e in entries if os.path.isdir(os.path.join(directory, e))]
    
    entries = [e for e in entries if e not in exclude_dirs]  # Exclude specified directories
    
    for index, entry in enumerate(entries):
        path = os.path.join(directory, entry)
        is_last = index == len(entries) - 1
        connector = "+-- " if is_last else "|-- "
        print(prefix + connector + entry)
        
        if os.path.isdir(path):
            extension = "    " if is_last else "|   "
            generate_tree(path, prefix + extension, folders_only, exclude_dirs)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Generate an ASCII directory tree.")
    parser.add_argument("directory", nargs="?", default=".", help="Target directory")
    parser.add_argument("--folders-only", action="store_true", help="Only display folders")
    parser.add_argument("--exclude", nargs="*", default=[], help="Directories to exclude")
    args = parser.parse_args()
    
    exclude_dirs = set(args.exclude) | {"venv", "env", "__pycache__"}  # Default exclusions
    print(args.directory)
    generate_tree(args.directory, folders_only=args.folders_only, exclude_dirs=exclude_dirs)



