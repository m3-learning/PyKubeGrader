#!/usr/bin/env bash

# Namespace where JupyterHub is deployed
NAMESPACE="jhub"

# Label to filter single-user pods
LABEL_SELECTOR="component=singleuser-server"

# The path in the container to copy
REMOTE_DIR="/user/"

# Local directory to store all user data
BACKUP_ROOT="E:\jhub_backup"

# Create the local backup directory
mkdir -p "$BACKUP_ROOT"

# Retrieve all single-user pod names
pods=$(kubectl get pods -n "${NAMESPACE}" \
            -l "${LABEL_SELECTOR}" \
            -o jsonpath='{.items[*].metadata.name}')

# Loop through each pod
for pod in $pods; do
  echo "Processing pod: $pod"

  # The single-user pod name is often jupyter-<username>. Trim off 'jupyter-' if that is the naming convention.
  # Adjust accordingly if your naming pattern differs.
  username=$(echo "$pod" | sed 's/^jupyter-//')

  # Print the derived username to confirm
  echo "  -> Extracted username: $username"

  # Create a local directory for this user
  user_backup_dir="${BACKUP_ROOT}/${username}"
  mkdir -p "$user_backup_dir"

  # Copy the remote user directory to the local folder
  echo "  -> Copying from $NAMESPACE/$pod:$REMOTE_DIR to $user_backup_dir"
  kubectl cp \
    "$NAMESPACE/$pod:$REMOTE_DIR" \
    "$user_backup_dir" \
    --retries=5

  echo "Finished copying user: $username"
  echo "--------------------------------"
done

echo "All user data has been copied to the '$BACKUP_ROOT' directory."
