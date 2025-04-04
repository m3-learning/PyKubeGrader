#!/usr/bin/env bash

# Namespace where JupyterHub is running (change if needed)
NAMESPACE="jhub"

# The local directory to store backups
BACKUP_ROOT="$HOME/jhub-backups"
mkdir -p "$BACKUP_ROOT"

# 1) Gather the list of JupyterHub PVCs (adjust grep/pattern as needed)
pvc_list=$(kubectl get pvc -n "$NAMESPACE" --no-headers | grep '^claim-' | awk '{print $1}')

if [[ -z "$pvc_list" ]]; then
  echo "No PVCs found matching pattern 'claim-' in namespace: $NAMESPACE"
  exit 0
fi

# 2) For each PVC, create ephemeral pod -> tar -> copy -> cleanup
for pvc in $pvc_list; do
  echo "--------------------------------"
  echo "Processing PVC: $pvc"

  # We'll create a random ephemeral pod name
  POD_NAME="copy-pod-${pvc}-$(head /dev/urandom | tr -dc a-z0-9 | head -c6)"

  # Create ephemeral pod spec
  cat <<EOF | kubectl apply -n "$NAMESPACE" -f -
apiVersion: v1
kind: Pod
metadata:
  name: $POD_NAME
spec:
  restartPolicy: Never
  containers:
    - name: copy-container
      image: ubuntu:22.04
      command: ["sleep"]
      args: ["3600"]
      volumeMounts:
        - name: vol
          mountPath: /data
  volumes:
    - name: vol
      persistentVolumeClaim:
        claimName: "$pvc"
EOF

  # Wait for the pod to be ready (or 60s timeout)
  echo "Waiting for pod $POD_NAME to become Ready..."
  kubectl wait --for=condition=Ready pod/"$POD_NAME" -n "$NAMESPACE" --timeout=60s || {
    echo "Pod $POD_NAME did not become ready in 60s, skipping..."
    kubectl -n "$NAMESPACE" delete pod "$POD_NAME" --force --grace-period=0
    continue
  }

  # 3) Tar up /data inside the pod and pipe to local .tar file
  backup_file="${BACKUP_ROOT}/${pvc}.tar"
  echo "Copying data from PVC=$pvc to $backup_file"

  kubectl exec -n "$NAMESPACE" "$POD_NAME" -- \
    bash -c 'cd /data && tar cf - ./' \
    > "$backup_file"

  # 4) Delete ephemeral pod
  kubectl -n "$NAMESPACE" delete pod "$POD_NAME" --force --grace-period=0

  echo "Finished backing up $pvc -> $backup_file"
done

echo "All done. Backups are in $BACKUP_ROOT"
