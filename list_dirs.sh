#!/bin/bash

# Check if at least one argument was provided
if [ "$#" -lt 1 ]; then
    echo "Usage: $0 <directory1> [directory2] ..."
    exit 1
fi

# Loop through all provided directory arguments
for dir in "$@"; do
    if [ -d "$dir" ]; then
        echo "=========================================="
        echo "Directory: $dir"
        echo "=========================================="
        
        # Use 'find' to locate all regular files while ignoring __pycache__ directories
        find "$dir" -type f -not -path "*/__pycache__/*" | while read -r file; do
            echo "----- File: $file -----"
            cat "$file"
            echo    # Blank line for readability
        done
        echo    # Extra blank line between directories
    else
        echo "Error: $dir is not a valid directory."
    fi
done

