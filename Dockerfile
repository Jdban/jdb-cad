# jdb-cad: the CAD toolchain (build123d, trimesh, ...) and the viewer server in one image.
# Usage: see README.md (docker compose up -d viewer; tools/cad part.py I5).
FROM python:3.13-slim

# fonts-dejavu-core: label.py engraves IDs with the system's bold sans font, and the engraving
# must match the frozen parts (they were made with DejaVu Sans Bold). libgl1/libglib: OpenCascade.
RUN apt-get update \
 && apt-get install -y --no-install-recommends fontconfig fonts-dejavu-core libgl1 libglib2.0-0 \
 && rm -rf /var/lib/apt/lists/*

COPY requirements-lock.txt /tmp/requirements-lock.txt
RUN pip install --no-cache-dir -r /tmp/requirements-lock.txt

# runs as the host user (compose.yaml), who has no home in the image
ENV HOME=/tmp MPLCONFIGDIR=/tmp/matplotlib PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /repo
