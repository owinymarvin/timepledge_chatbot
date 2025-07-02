import asyncio
import chromadb

async def main():
    client = await chromadb.AsyncHttpClient(host='vector-db', port=8000)

    collection = await client.get_or_create_collection(name="dmarv_collection")
    await collection.upsert(
        ids=["id1", "id2"],
        documents=[
            "This is a document about pineapple",
            "This is a document about oranges"
        ]
    )
    results = await collection.query(
        query_texts=["This is a query document about hawaii"],
        n_results=2
    )
    print(results)


asyncio.run(main())