#!/bin/bash

# Dependency analysis script for rust projects
echo "🔍 Analyzing dependencies across rust projects..."
echo

# Create temp file for collecting dependencies
temp_file="/tmp/rust_deps_$$"

# Find all Cargo.toml files and extract dependencies
find /home/xnull/repos/code/rust -name "Cargo.toml" -type f | while read cargo_file; do
    # Skip target directories
    if [[ "$cargo_file" =~ /target/ ]]; then
        continue
    fi

    project_dir=$(dirname "$cargo_file")
    project_name=$(basename "$project_dir")

    echo "📦 $project_name"

    # Extract dependencies using grep and sed
    grep -A 100 "^\[dependencies\]" "$cargo_file" | grep -B 100 "^\[" | head -n -1 | tail -n +2 | grep "^[a-zA-Z]" | while read line; do
        dep_name=$(echo "$line" | cut -d'=' -f1 | xargs)
        dep_version=$(echo "$line" | sed 's/.*"\([^"]*\)".*/\1/' | head -c 20)
        echo "$dep_name|$dep_version|$project_name" >> "$temp_file"
    done
done

echo
echo "📊 Dependency Summary by Name:"
echo

# Sort and group dependencies
if [ -f "$temp_file" ]; then
    sort "$temp_file" | awk -F'|' '
    {
        dep = $1
        version = $2
        project = $3

        if (dep != last_dep && last_dep != "") {
            print ""
        }

        if (dep != last_dep) {
            printf "🔧 %s:\n", dep
            last_dep = dep
        }

        printf "  %-20s -> %s\n", project, version
    }'

    rm "$temp_file"
fi

echo
echo "✅ Analysis complete!"