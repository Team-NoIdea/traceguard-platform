# TraceGuard backend — dev/hackathon image.
# Python 3.12 is pinned deliberately: see README "Why Python 3.12" section
# (host machines on 3.14 hit pydantic-core Rust source builds; 3.12 has
# prebuilt wheels for our pinned pydantic-core version).

FROM python:3.12-slim

WORKDIR /app

# Install dependencies first so this layer is cached and doesn't
# re-run on every code change.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application code (routes/, schemas/, services/, mock-data/, main.py).
# In dev, docker-compose bind-mounts the repo over this anyway so
# --reload picks up local edits; this COPY is what makes the image
# runnable standalone (e.g. `docker run` with no compose/volumes).
COPY . .

EXPOSE 8000

# --reload is fine for this hackathon-stage dev image. Drop it for a
# real prod image later (and don't bind-mount source over it).
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
