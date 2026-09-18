# ============================================================
# Smart Knowledge Gap — Makefile
# ============================================================

.PHONY: help install run test docker-build docker-up docker-down clean

help:
 @echo "Available commands:"
 @echo "  make install       - Install Python dependencies"
 @echo "  make run           - Run Flask dev server"
 @echo "  make test          - Run the full test suite"
 @echo "  make docker-build  - Build Docker image"
 @echo "  make docker-up     - Start Docker Compose"
 @echo "  make docker-down   - Stop Docker Compose"
 @echo "  make clean         - Clean caches and temp files"

install:
 pip install --upgrade pip
 pip install -r requirements.txt

run:
 python app/app.py

test:
 SECRET_KEY=test PYTHONPATH=app python tests/test_full_flow.py

docker-build:
 docker build -t smart-knowledge-gap:latest .

docker-up:
 docker compose up -d

docker-down:
 docker compose down

clean:
 find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
 find . -type f -name "*.pyc" -delete
 rm -f data/test.db data/smart_knowledge_gap.db
