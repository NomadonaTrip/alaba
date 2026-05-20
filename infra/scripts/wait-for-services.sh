#!/bin/sh
set -e

cd "$(dirname "$0")/.."

echo "Waiting for foundation services to be healthy..."

# All foundation services must be healthy
for service in postgres redis minio; do
  echo -n "  $service: "
  until [ "$(docker inspect -f '{{.State.Health.Status}}' alaba-$service 2>/dev/null)" = "healthy" ]; do
    echo -n "."
    sleep 2
  done
  echo " healthy"
done

# minio-init must have completed (one-shot)
until [ "$(docker inspect -f '{{.State.Status}}' alaba-minio-init 2>/dev/null)" = "exited" ]; do
  echo "  Waiting for minio-init to complete..."
  sleep 2
done

echo "All foundation services ready."
