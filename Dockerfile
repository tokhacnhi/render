name: Build & Push Docker Image

on:
  push:
    branches: [ "main" ]
    paths:
      - "dockerbox/render/Dockerfile"
      - "requirements.txt"

jobs:
  build-and-push:
    runs-on: ubuntu-latest
    permissions:
      packages: write  # cần để push GHCR
      contents: read

    steps:
      - uses: actions/checkout@v5

      # Login GHCR tự động với token workflow
      - name: Login to GHCR
        uses: docker/login-action@v2
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      # Build + push image
      - name: Build & Push
        run: |
          docker build --platform=linux/amd64 \
            -t ghcr.io/${{ github.repository }}/render-base:latest \
            -f dockerbox/render/Dockerfile .
          docker push ghcr.io/${{ github.repository }}/render-base:latest