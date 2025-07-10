from fastapi import FastAPI, UploadFile, File, BackgroundTasks
from fastapi.responses import StreamingResponse
from typing import List
from pathlib import Path
import shutil
from contextlib import asynccontextmanager

from src.chroma_handler import check_if_already_embedded, embed_document
from src.chatbot import (
    ask_with_context,
    stream_response,
    get_chat_history,
    list_user_chats,
    delete_chat
)
from src.schemas import (
    SchemaUploadResponse,
    SchemaFileUploadStatus,
    SchemaAskRequest,
    SchemaAskResponse,
    SchemaChatMessage
)
from src.config import PDF_INPUT_DIR

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🔄 Checking for unembedded PDFs on startup...")
    for file in PDF_INPUT_DIR.glob("*.pdf"):
        print(f"🔍 Scanning file: {file.name}")
        doc_hash = await check_if_already_embedded(file)
        if doc_hash:
            print(f"📥 Embedding {file.name}...")
            await embed_document(file, doc_hash)
        else:
            print(f"✅ Already embedded: {file.name}")
    yield
    print("🛑 App is shutting down.")

app = FastAPI(lifespan=lifespan)


@app.post("/api/upload", response_model=SchemaUploadResponse)
async def upload_pdfs(
    files: List[UploadFile] = File(...),
    background_tasks: BackgroundTasks = None
):
    print("📤 Upload endpoint hit with", len(files), "file(s)")
    responses: List[SchemaFileUploadStatus] = []

    for file in files:
        print(f"📂 Processing upload: {file.filename}")

        if not file.filename.endswith(".pdf"):
            print(f"❌ Skipped {file.filename} (invalid type)")
            responses.append(SchemaFileUploadStatus(
                filename=file.filename,
                status="skipped",
                message="Invalid file type. Only PDF files are supported."
            ))
            continue

        file_path = PDF_INPUT_DIR / file.filename
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        print(f"✅ Saved {file.filename} to {file_path}")

        doc_hash = await check_if_already_embedded(file_path)
        if doc_hash is None:
            print(f"⚠️ Skipping {file.filename}, already embedded")
            responses.append(SchemaFileUploadStatus(
                filename=file.filename,
                status="skipped",
                message="File already embedded based on content hash."
            ))
        else:
            print(f"🚀 Starting embedding for {file.filename}")
            background_tasks.add_task(embed_document, file_path, doc_hash)
            responses.append(SchemaFileUploadStatus(
                filename=file.filename,
                status="started",
                message="File is being processed and embedded in the background."
            ))

    print("📤 Upload response:", responses)
    return SchemaUploadResponse(results=responses)


@app.post("/api/chat", response_model=SchemaAskResponse)
async def chat(request: SchemaAskRequest):
    print(f"💬 Received chat message from user {request.user_id}, chat {request.chat_id}")
    result = await ask_with_context(
        user_id=request.user_id,
        chat_id=request.chat_id,
        question=request.question
    )
    print("🤖 Chatbot response generated.")
    return SchemaAskResponse(**result)


@app.post("/api/chat/stream")
async def stream_chat(request: SchemaAskRequest):
    print(f"🌊 Streaming chat for user {request.user_id}, chat {request.chat_id}")
    stream = stream_response(
        user_id=request.user_id,
        chat_id=request.chat_id,
        question=request.question
    )
    return StreamingResponse(stream, media_type="text/plain")


@app.get("/api/history/{user_id}/{chat_id}", response_model=List[SchemaChatMessage])
async def get_history(user_id: str, chat_id: str):
    print(f"📜 Fetching history for user {user_id}, chat {chat_id}")
    return get_chat_history(user_id, chat_id)


@app.get("/api/user/{user_id}/chats", response_model=List[str])
async def get_user_chats(user_id: str):
    print(f"📁 Listing chats for user {user_id}")
    return list_user_chats(user_id)


@app.delete("/api/history/{user_id}/{chat_id}")
async def delete_chat_history(user_id: str, chat_id: str):
    print(f"🗑️ Deleting chat history for user {user_id}, chat {chat_id}")
    delete_chat(user_id, chat_id)
    return {"status": "deleted"}
