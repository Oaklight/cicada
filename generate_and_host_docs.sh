#!/bin/bash

# Ensure the PATH includes standard directories
export PATH="/bin:/usr/bin:/usr/local/bin:$PATH"

# Dynamically determine the paths to commands
declare -A COMMANDS=(
    ["FIND"]="$(which find)"
    ["BASENAME"]="$(which basename)"
    ["DIRNAME"]="$(which dirname)"
    ["REALPATH"]="$(which realpath)"
    ["MKDIR"]="$(which mkdir)"
    ["PDOC"]="$(which pdoc)"
    ["SED"]="$(which sed)"
    ["GREP"]="$(which grep)"
    ["RSYNC"]="$(which rsync)"
    ["SSH"]="$(which ssh)"
    ["CAT"]="$(which cat)"
)

# Verify all commands are available
for CMD in "${!COMMANDS[@]}"; do
    if [[ -z "${COMMANDS[$CMD]}" ]]; then
        echo "Error: Command '$CMD' not found. Please install it and ensure it's in your PATH."
        exit 1
    fi
    declare "$CMD=${COMMANDS[$CMD]}"
done

# Variables
REPO_DIR="./"
DOCS_DIR="$REPO_DIR/docs"
INCLUDE_FILE="$REPO_DIR/docs/include.txt"
SERVER_HOST="cloud.jpn2"
SERVER_USER="root" # Assuming you are using root for rsync
SERVER_DOCS_DIR="/var/www/projects/codecad/docs"

# Function to generate documentation for a single module
generate_docs() {
    local MODULE="$1"
    local MODULE_NAME=$("$BASENAME" "$MODULE" .py)
    local MODULE_DIR=$("$DIRNAME" "$MODULE")
    local RELATIVE_PATH=$("$REALPATH" --relative-to="$REPO_DIR" "$MODULE_DIR")
    local OUTPUT_DIR="$DOCS_DIR/$RELATIVE_PATH"

    "$MKDIR" -p "$OUTPUT_DIR"
    echo "Processing: $MODULE"
    "$PDOC" -o "$OUTPUT_DIR" "$MODULE"
    echo "Generated docs for $MODULE"
}

# Function to create the overarching index.html
create_index_html() {
    echo "Creating overarching index.html..."
    "$CAT" <<EOF >"$DOCS_DIR/index.html"
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Project Documentation</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 20px;
        }
        h1 {
            color: #333;
        }
        ul {
            list-style-type: none;
            padding: 0;
        }
        li {
            margin: 10px 0;
        }
        a {
            text-decoration: none;
            color: #007BFF;
        }
        a:hover {
            text-decoration: underline;
        }
    </style>
</head>
<body>
    <h1>Project Documentation</h1>
    <p>Welcome to the documentation for the project. Below are links to the documentation for each module:</p>
    <ul>
EOF

    # Add links for each module
    for PATH in "${INCLUDED_PATHS[@]}"; do
        PATH=$("$SED" -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//' <<<"$PATH" | "$GREP" -v '^#')
        if [[ -z "$PATH" ]]; then
            continue # Skip empty lines
        fi

        MODULE_NAME=$("$BASENAME" "$PATH")
        echo "        <li><a href=\"$PATH/index.html\">$MODULE_NAME Module</a></li>" >>"$DOCS_DIR/index.html"
    done

    "$CAT" <<EOF >>"$DOCS_DIR/index.html"
    </ul>
</body>
</html>
EOF
}

# Function to update only the index.html
update_index_only() {
    echo "Updating only the index.html..."
    create_index_html
    echo "index.html has been updated."
}

# Function to sync documentation to the remote server and set ownership
sync_to_remote() {
    echo "Creating target directory on the remote server if it doesn't exist..."
    "$SSH" "$SERVER_USER@$SERVER_HOST" "mkdir -p $SERVER_DOCS_DIR"
    if [[ $? -ne 0 ]]; then
        echo "Error: Failed to create target directory on the remote server."
        exit 1
    fi
    echo "Target directory has been created (if it didn't exist)."

    echo "Syncing documentation to the remote server using rsync..."
    "$RSYNC" --rsh="$SSH" -avz --delete "$DOCS_DIR/" "$SERVER_USER@$SERVER_HOST:$SERVER_DOCS_DIR/"
    if [[ $? -ne 0 ]]; then
        echo "Error: Failed to sync documentation to the remote server."
        exit 1
    fi
    echo "Documentation has been synced to the remote server."

    echo "Setting ownership to caddy:caddy on the remote server..."
    "$SSH" "$SERVER_USER@$SERVER_HOST" "chown -R caddy:caddy $SERVER_DOCS_DIR"
    if [[ $? -ne 0 ]]; then
        echo "Error: Failed to set ownership on the remote server."
        exit 1
    fi
    echo "Ownership has been set to caddy:caddy."
}

# Step 1: Read paths to include from include.txt
echo "Reading paths to include from $INCLUDE_FILE..."
if [[ ! -f "$INCLUDE_FILE" ]]; then
    echo "Error: include.txt not found in $REPO_DIR/docs"
    exit 1
fi

# Read paths from include.txt into an array
mapfile -t INCLUDED_PATHS <"$INCLUDE_FILE"

# Check if the script should only update the index.html
if [[ "$1" == "--update-index" ]]; then
    update_index_only
    sync_to_remote
    exit 0
fi

# Step 2: Generate Documentation
echo "Generating documentation..."
"$MKDIR" -p "$DOCS_DIR"
for PATH in "${INCLUDED_PATHS[@]}"; do
    # Remove leading/trailing whitespace and comments (lines starting with #)
    PATH=$("$SED" -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//' <<<"$PATH" | "$GREP" -v '^#')
    if [[ -z "$PATH" ]]; then
        continue # Skip empty lines
    fi

    # Find all Python modules in the specified path
    MODULES=$("$FIND" "$REPO_DIR/$PATH" -type f -name "*.py" ! -name "__init__.py" ! -name "test*.py")
    if [[ -z "$MODULES" ]]; then
        echo "No modules found in $PATH"
        continue
    fi

    for MODULE in $MODULES; do
        generate_docs "$MODULE"
    done
done

# Step 3: Create Overarching index.html
create_index_html

# Step 4: Sync Documentation to Server
sync_to_remote

echo "Documentation has been generated and hosted on your server."
