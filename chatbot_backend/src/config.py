# config.py

from pathlib import Path

CHROMA_HOST = "vector-db"
CHROMA_PORT = 8000
COLLECTION_NAME = "uganda_law_and_land_docs"

PDF_INPUT_DIR = Path("./documents/inputs")
TEXT_OUTPUT_DIR = Path("./documents/outputs")
