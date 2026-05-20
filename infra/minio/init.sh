#!/bin/sh
set -e

# Wait for MinIO to be ready
until mc alias set local http://minio:9000 "$MINIO_ROOT_USER" "$MINIO_ROOT_PASSWORD"; do
  echo "Waiting for MinIO..."
  sleep 1
done

# Create buckets (idempotent)
mc mb --ignore-existing local/alaba-source
mc mb --ignore-existing local/alaba-transcoded
mc mb --ignore-existing local/alaba-previews

# Set lifecycle on previews bucket (90-day expiry)
cat > /tmp/lifecycle.json <<EOF
{
  "Rules": [
    {
      "ID": "expire-previews-90d",
      "Status": "Enabled",
      "Expiration": {"Days": 90}
    }
  ]
}
EOF
mc ilm import local/alaba-previews < /tmp/lifecycle.json || true

echo "MinIO buckets ready."
