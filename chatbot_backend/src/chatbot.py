import uuid
import sqlite3
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, AsyncGenerator

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from src.chroma_handler import query_documents
from dotenv import load_dotenv

load_dotenv()
DB_PATH = Path("chat_history.db")

# setup the DB and initialise it
def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS chat_history (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                chat_id TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('system', 'human', 'ai')),
                message TEXT NOT NULL,
                timestamp TEXT NOT NULL
            )
        ''')
        conn.execute('''
            CREATE INDEX IF NOT EXISTS idx_user_chat ON chat_history(user_id, chat_id)
        ''')

def save_message(user_id: str, chat_id: str, role: str, message: str):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            '''INSERT INTO chat_history (id, user_id, chat_id, role, message, timestamp)
               VALUES (?, ?, ?, ?, ?, ?)''',
            (str(uuid.uuid4()), user_id, chat_id, role, message, datetime.now().isoformat())
        )

def has_existing_chat(user_id: str, chat_id: str) -> bool:
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute(
            '''SELECT 1 FROM chat_history WHERE user_id = ? AND chat_id = ? LIMIT 1''',
            (user_id, chat_id)
        )
        return cursor.fetchone() is not None

def get_chat_history(user_id: str, chat_id: str) -> List[Dict]:
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute(
            '''SELECT role, message, timestamp FROM chat_history
               WHERE user_id = ? AND chat_id = ?
               ORDER BY timestamp ASC''',
            (user_id, chat_id)
        )
        return [
            {"role": row[0], "message": row[1], "timestamp": row[2]}
            for row in cursor.fetchall()
        ]

def list_user_chats(user_id: str) -> List[str]:
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute(
            '''SELECT DISTINCT chat_id FROM chat_history WHERE user_id = ?''',
            (user_id,)
        )
        return [row[0] for row in cursor.fetchall()]

def delete_chat(user_id: str, chat_id: str):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            '''DELETE FROM chat_history WHERE user_id = ? AND chat_id = ?''',
            (user_id, chat_id)
        )



# Initialise message History DB
init_db()

SYSTEM_PROMPT = "You are a helpful legal assistant. Use the provided legal context to answer questions clearly."

llm = ChatGroq(
    model="meta-llama/llama-4-scout-17b-16e-instruct",
    temperature=0.3,
    max_tokens=1024,
    groq_api_key=os.getenv("GROQ_API_KEY")
)

async def ask_with_context(user_id: str, chat_id: Optional[str], question: str) -> Dict[str, str]:
    if not chat_id:
        chat_id = str(uuid.uuid4())

    if not has_existing_chat(user_id, chat_id):
        save_message(user_id, chat_id, "system", SYSTEM_PROMPT)
    save_message(user_id, chat_id, "human", question)

    results = await query_documents(question, top_k=5)
    context = "\n\n".join(results["documents"][0])

    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("human", "Context:\n{context}\n\nQuestion: {question}")
    ])
    chain = prompt | llm
    response = chain.invoke({"context": context, "question": question})
    
    save_message(user_id, chat_id, "ai", str(response.content))
    return {"user_id": user_id, "chat_id": chat_id, "answer": response.content}

async def stream_response(user_id: str, chat_id: Optional[str], question: str) -> AsyncGenerator[str, None]:
    result = await ask_with_context(user_id, chat_id, question)
    yield result["answer"]
