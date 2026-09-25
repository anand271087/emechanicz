#!/bin/sh
# Run the API with auto-reload for local development.
cd "$(dirname "$0")" && exec .venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
