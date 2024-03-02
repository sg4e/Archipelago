#!/bin/bash

# Get the current directory
folder=$(dirname "$0")

# Create a temporary directory
temp_dir=$(mktemp -d)
mkdir $temp_dir/fm

# Move into the folder
cd "$folder" || exit

# Get all files in the folder (excluding directories and the script file itself)
files=()
script_name=$(basename "$0")

while IFS= read -r -d $'\0' file; do
    if [[ ! -d "$file" && "$file" != "$script_name" ]]; then
        files+=("$file")
    fi
done < <(find . -maxdepth 1 -type f ! -name "$script_name" -print0)

# Sign each file with GPG
for file in "${files[@]}"; do
    gpg --output "$temp_dir/fm/$(basename "$file").sig" --detach-sign --digest-algo SHA256 "$file"
done

cp "${files[@]}" "$temp_dir/fm"

cd "$temp_dir" || exit

# Zip the files along with their signatures
zip -r "fm.apworld" .

cd "$folder" || exit

cp "$temp_dir/fm.apworld" "$HOME"

# Clean up temporary directory
rm -rf "$temp_dir"

echo "Files signed with GPG and zipped successfully."
echo "Don't forget to increment the version!"
