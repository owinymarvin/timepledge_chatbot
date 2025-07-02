from typing import Union
from fastapi import FastAPI
from .chroma import results

app = FastAPI()

@app.get("/")
async def read_root():
    return results