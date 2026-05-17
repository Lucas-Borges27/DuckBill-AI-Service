#!/bin/bash
set -e

IMAGE="lucasbsouza0/duckbill-ai-service"
TAG="${1:-latest}"

echo "==> Building $IMAGE:$TAG"
echo "    Build context: $(pwd)"

docker build \
  --file docker/Dockerfile \
  --tag "$IMAGE:$TAG" \
  --tag "$IMAGE:latest" \
  .

echo ""
echo "==> Pushing $IMAGE:$TAG"
docker push "$IMAGE:$TAG"

if [ "$TAG" != "latest" ]; then
  docker push "$IMAGE:latest"
fi

echo ""
echo "Done! Pull with:"
echo "  docker pull $IMAGE:$TAG"
