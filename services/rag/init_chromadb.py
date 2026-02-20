#!/usr/bin/env python3
"""
Code Generation for Jr Engineer
Based on Devika AI architecture patterns
Cherokee AI Federation - For Seven Generations

Created: January 17, 2026
"""

import os

# Step 1: Create /ganuda/services/rag/install_deps.sh
install_deps_script = """#!/bin/bash
set -e
cd /ganuda/services/rag
pip install chromadb sentence-transformers requests lxml
mkdir -p /ganuda/data/chromadb
mkdir -p /ganuda/data/regulations
echo "Dependencies installed successfully"
pip list | grep -E "chroma|sentence|lxml"
"""

with open("/ganuda/services/rag/install_deps.sh", "w") as file:
    file.write(install_deps_script)

# Make the script executable
os.chmod("/ganuda/services/rag/install_deps.sh", 0o755)

# Step 2: Create /ganuda/services/rag/init_chromadb.py
init_chromadb_script = """import chromadb
from chromadb.config import Settings

# Initialize persistent client
client = chromadb.Client(Settings(
    persist_directory="/ganuda/data/chromadb"
))

# Create or get collection named va_regulations with cosine distance
collection = client.get_or_create_collection(name="va_regulations", metric="cosine")

# Print collection info and count
print(f"Collection Name: {collection.name}")
print(f"Collection Count: {collection.count()}")
"""

with open("/ganuda/services/rag/init_chromadb.py", "w") as file:
    file.write(init_chromadb_script)