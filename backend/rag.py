import voyageai
import chromadb

import config

_vo = None
_collection = None


def _get_client():
    global _vo, _collection
    if _vo is None:
        _vo = voyageai.Client(api_key=config.VOYAGE_API_KEY)
    if _collection is None:
        client = chromadb.PersistentClient(path=config.CHROMA_DB_PATH)
        _collection = client.get_or_create_collection(
            name=config.COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
    return _vo, _collection


def retrieve_context(query: str, n_results: int = 5, topic: str | None = None) -> list[dict]:
    vo, collection = _get_client()

    result = vo.embed([query], model=config.EMBEDDING_MODEL, input_type="query")
    query_embedding = result.embeddings[0]

    where_filter = {"topic": topic} if topic else None

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        where=where_filter,
        include=["documents", "metadatas", "distances"],
    )

    chunks = []
    for i in range(len(results["ids"][0])):
        chunks.append({
            "text": results["documents"][0][i],
            "metadata": results["metadatas"][0][i],
            "distance": results["distances"][0][i],
        })

    return chunks


def get_topics() -> list[str]:
    _, collection = _get_client()
    all_meta = collection.get(include=["metadatas"])
    topics = sorted({m["topic"] for m in all_meta["metadatas"]})
    return topics


def get_collection_count() -> int:
    _, collection = _get_client()
    return collection.count()
