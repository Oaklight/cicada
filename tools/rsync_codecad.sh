#!/bin/bash
# This script is used to sync codecad-rag repo with remote dev machine, you shall change the DEST to your remote dev machine.
# The default action is push, which means push local changes to remote dev machine.
# You can also use --pull to pull changes from remote dev machine to local.
# You can also use -e or --exclude to exclude some files or directories from the sync.
# You can also use -s or --source to specify the source directory to sync. The default is the current directory.
# You can also use -d or --dest to specify the destination directory to sync. The default is ~/projects/codecad/codecad-rag on the remote dev machine.

# use with caution, this script will overwrite files on the remote dev machine.

# Default values
ACTION="push"
EXCLUDE="MiniGPT-3D/params_weight"
SOURCE="./"
DEST="lambda12:~/projects/codecad/codecad-rag/"

# Parse command-line arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
    --pull) ACTION="pull" ;;
    --push) ACTION="push" ;;
    -e | --exclude)
        EXCLUDE="$2"
        shift
        ;;
    -s | --source)
        SOURCE="$2"
        shift
        ;;
    -d | --dest)
        DEST="$2"
        shift
        ;;
    *)
        echo "Unknown parameter passed: $1"
        exit 1
        ;;
    esac
    shift
done

# Perform the rsync operation
if [[ "$ACTION" == "push" ]]; then
    rsync -rP --exclude="$EXCLUDE" "$SOURCE" "$DEST"
elif [[ "$ACTION" == "pull" ]]; then
    rsync -rP --exclude="$EXCLUDE" "$DEST" "$SOURCE"
fi
