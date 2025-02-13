#!/usr/bin/env python3
"""
Project File Collector Script
Copies relevant project files to a flat directory structure for documentation
and knowledge management purposes.
"""

import os
import shutil
from datetime import datetime
from pathlib import Path
import argparse

# File patterns to include
INCLUDE_PATTERNS = [
    "*.py",    # Python source files
    "*.md",    # Documentation
    "*.txt",   # Text files
    "*.env*",  # Environment files (including .env.example)
    "*.yaml",  # YAML configuration files
    "*.json",  # JSON files
    "*.ini",   # INI configuration files
    "*.cfg",   # Config files
    "*.toml",  # TOML files (including pyproject.toml)
]

def should_process_directory(dir_path: str) -> bool:
    """Check if directory should be processed."""
    dir_parts = Path(dir_path).parts
    
    # Exclude standard system directories and previous output directories
    exclude_patterns = {
        "__pycache__",
        ".venv",
        "venv",
        "env",
        ".env",
        ".git",
        ".pytest_cache",
        "node_modules",
        ".idea",
        ".vscode",
        "dist",
        "build",
        "*.egg-info",
        "project_knowledge",  # Exclude previous output directories
        "project_files_"      # Exclude timestamped directories
    }
    
    return not any(part in exclude_patterns or part.startswith("project_files_") 
                  for part in dir_parts)

def verify_directory_access(path: Path) -> None:
    """Verify we can actually write to the directory."""
    if not path.exists():
        raise RuntimeError(f"Directory does not exist: {path}")
    
    # Try to create a test file
    test_file = path / ".write_test"
    try:
        test_file.write_text("test")
        test_file.unlink()  # Clean up
    except Exception as e:
        raise RuntimeError(f"Cannot write to directory {path}: {e}")

def collect_files(source_dir: str, target_dir: str, prefix: str = "") -> None:
    """
    Recursively collect files from source directory and copy to target directory.
    
    Args:
        source_dir: Source directory to collect files from
        target_dir: Target directory to copy files to
        prefix: Optional prefix for target filenames
    """
    source_path = Path(source_dir)
    target_path = Path(target_dir)
    
    # Create target directory if it doesn't exist
    target_path.mkdir(parents=True, exist_ok=True)
    
    # Track copied files for summary
    copied_files = []
    
    # Walk through source directory
    for root, dirs, files in os.walk(source_dir):
        # Skip excluded directories
        if not should_process_directory(root):
            continue
            
        print(f"\nChecking directory: {root}")
        for file in files:
            print(f"  Checking file: {file}")
            source_file = Path(root) / file
            
            # Check if file matches include patterns
            if not any(source_file.match(pattern) for pattern in INCLUDE_PATTERNS):
                continue
                
            # Generate target filename - simplify naming scheme
            rel_path = source_file.relative_to(source_path)
            rel_parts = rel_path.parts
            if len(rel_parts) > 1:
                # Use only the immediate parent directory name
                target_name = f"{rel_parts[-2]}_{file}" 
                target_name = file  
            else:
                target_name = file
                
            # Clean up the target name to avoid any issues
            target_name = target_name.replace('__', '_')
            target_file = target_path / target_name
            
            try:
                print(f"  Copying: {source_file} -> {target_file}")
                shutil.copy2(source_file, target_file)
                
                # Verify the file was actually created
                if not target_file.exists():
                    raise RuntimeError(f"File copy succeeded but file doesn't exist at destination")
                    
                copied_files.append((str(rel_path), target_name))
                print(f"  ✓ Successfully copied: {target_name}")
            except Exception as e:
                print(f"  Error copying {source_file}: {str(e)}")
    
    return copied_files

def main():
    parser = argparse.ArgumentParser(description="Collect project files into a flat directory structure")
    parser.add_argument("source", help="Source project directory")
    parser.add_argument("target", help="Target directory for collected files")
    parser.add_argument("--prefix", help="Optional prefix for target filenames", default="")
    
    args = parser.parse_args()
    
    # Handle paths correctly whether run from scripts dir or project root
    source_dir = Path(args.source).resolve()
    # Create target directory relative to current working directory, not scripts directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    target_dir = Path(os.getcwd()) / args.target / f"project_files_{timestamp}"
    
    print(f"\nSource directory: {source_dir}")
    print(f"Target directory: {target_dir}")
    
    try:
        # Create and verify target parent directory
        target_parent = target_dir.parent
        target_parent.mkdir(parents=True, exist_ok=True)
        verify_directory_access(target_parent)
        print(f"✓ Target parent directory is writable")
        
        # Create collection directory
        target_dir.mkdir(parents=False)
        verify_directory_access(target_dir)
        print(f"✓ Created collection directory: {target_dir}")
        
        # Collect files
        copied_files = collect_files(source_dir, target_dir, args.prefix)
        
        # Generate summary report
        summary_file = target_dir / "collection_summary.md"
        with open(summary_file, "w", encoding='utf-8') as f:
            f.write("# Project Files Collection Summary\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("## Collected Files\n\n")
            for source, target in sorted(copied_files):
                f.write(f"* {source} -> {target}\n")
        
        print(f"\nCollection complete! {len(copied_files)} files copied.")
        print(f"Summary written to: {summary_file}")
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return

if __name__ == "__main__":
    main()
    
    
    
    
    