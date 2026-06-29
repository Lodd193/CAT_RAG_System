import chromadb
import voyageai

import config

_voyage_client = None
_collection = None


def _get_voyage():
    global _voyage_client
    if _voyage_client is None:
        _voyage_client = voyageai.Client(api_key=config.VOYAGE_API_KEY)
    return _voyage_client


def _get_collection():
    global _collection
    if _collection is None:
        client = chromadb.PersistentClient(path=config.CHROMA_PERSIST_DIR)
        _collection = client.get_or_create_collection(config.CHROMA_COLLECTION)
    return _collection


def chunk_text(text: str) -> list[str]:
    """Split text into overlapping word-count chunks."""
    words = text.split()
    chunks, i = [], 0
    while i < len(words):
        chunks.append(" ".join(words[i : i + config.CHUNK_SIZE]))
        i += config.CHUNK_SIZE - config.CHUNK_OVERLAP
    return chunks


def embed_and_store(doc_id: str, doc_name: str, text: str) -> int:
    """Chunk, embed with Voyage AI, upsert into ChromaDB. Returns chunk count."""
    voyage = _get_voyage()
    collection = _get_collection()
    chunks = chunk_text(text)
    if not chunks:
        return 0
    embeddings = voyage.embed(chunks, model=config.VOYAGE_MODEL, input_type="document").embeddings
    ids = [f"{doc_id}_{i}" for i in range(len(chunks))]
    metadatas = [{"doc_id": doc_id, "doc_name": doc_name, "chunk_index": i} for i in range(len(chunks))]
    collection.upsert(ids=ids, embeddings=embeddings, documents=chunks, metadatas=metadatas)
    return len(chunks)


def search(query: str) -> list[dict]:
    """Return top-K most relevant archive chunks for a query. Empty list if archive is empty."""
    collection = _get_collection()
    if collection.count() == 0:
        return []
    voyage = _get_voyage()
    query_emb = voyage.embed([query], model=config.VOYAGE_MODEL, input_type="query").embeddings[0]
    results = collection.query(
        query_embeddings=[query_emb],
        n_results=min(config.TOP_K_CHUNKS, collection.count()),
        include=["documents", "metadatas"],
    )
    chunks = []
    for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
        chunks.append({"text": doc, "doc_name": meta.get("doc_name", "Unknown")})
    return chunks


def archive_chunk_count() -> int:
    return _get_collection().count()
