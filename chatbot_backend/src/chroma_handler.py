import hashlib
import re
from pathlib import Path
from docling.document_converter import DocumentConverter
from langchain_text_splitters import RecursiveCharacterTextSplitter
import chromadb

from src.config import (
    CHROMA_HOST,
    CHROMA_PORT,
    COLLECTION_NAME,
    TEXT_OUTPUT_DIR
)

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200


def compute_file_hash(file_path: Path) -> str:
    return hashlib.sha256(file_path.read_bytes()).hexdigest()


def split_structured_text(text: str) -> list[str]:
    splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
    heading_pattern = r"^##\s+\d+\. .+$"
    heading_regex = re.compile(heading_pattern, flags=re.MULTILINE)

    matches = list(heading_regex.finditer(text))
    sections = []

    for i, match in enumerate(matches):
        start = match.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        section = text[start:end].strip()
        if section:
            split_chunks = splitter.split_text(section)
            sections.extend(split_chunks)

    return sections


async def check_if_already_embedded(file_path: Path) -> str | None:
    doc_hash = compute_file_hash(file_path)
    client = await chromadb.AsyncHttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
    collection = await client.get_or_create_collection(name=COLLECTION_NAME)

    try:
        existing = await collection.get(ids=[f"{doc_hash}-0"])
        if existing["ids"]:
            return None
    except Exception:
        pass

    return doc_hash


async def embed_document(file_path: Path, doc_hash: str) -> None:
    try:
        client = await chromadb.AsyncHttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
        collection = await client.get_or_create_collection(name=COLLECTION_NAME)

        converter = DocumentConverter()
        result = converter.convert(file_path)
        extracted_text = result.document.export_to_text()

        TEXT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        output_path = TEXT_OUTPUT_DIR / f"{file_path.stem}.txt"
        output_path.write_text(extracted_text, encoding="utf-8")

        chunks = split_structured_text(extracted_text)
        total = len(chunks)

        ids = [f"{doc_hash}-{i}" for i in range(total)]
        metadatas = [
            {
                "source_file": file_path.name,
                "chunk": f"{i+1} of {total}"
            }
            for i in range(total)
        ]

        await collection.upsert(documents=chunks, ids=ids, metadatas=metadatas)
        print(f"🐐 Embedding complete: {file_path.name}, your the 🐐")

    except Exception as e:
        print(f"😭 Failed embedding {file_path.name}: {e}")


async def query_documents(question: str, top_k: int = 5) -> dict:
    client = await chromadb.AsyncHttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
    collection = await client.get_or_create_collection(name=COLLECTION_NAME)

    results = await collection.query(
        query_texts=[question],
        n_results=top_k
    )
    return results
