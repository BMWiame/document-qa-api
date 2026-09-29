from database import SessionLocal
from embed import get_embedding
from models import Chunk
from sqlalchemy import or_

def search_chunk(question: str, top_k: int = 5):
    db = SessionLocal()
    embedded_question = get_embedding(question)
    results = (
        db.query(Chunk)
        .order_by(Chunk.embedding.cosine_distance(embedded_question))
        .limit(top_k)
        .all()
    )
    db.close()
    return results




def search_chunk_in_document(question: str, document_id: int, top_k: int = 5):
    db = SessionLocal()
    embedded_question = get_embedding(question)

    semantic_results = (
        db.query(Chunk)
        .filter(Chunk.document_id == document_id)
        .order_by(Chunk.embedding.cosine_distance(embedded_question))
        .limit(top_k)
        .all()
    )

    keywords = [w for w in question.split() if len(w) > 0]
    keyword_results = []
    if keywords:
        conditions = [Chunk.content.ilike(f"%{kw}%") for kw in keywords]
        keyword_results = (
            db.query(Chunk)
            .filter(Chunk.document_id == document_id)
            .filter(or_(*conditions))
            .limit(top_k)
            .all()
        )

    seen_ids = set()
    combined = []
    for c in semantic_results + keyword_results:
        if c.id not in seen_ids:
            seen_ids.add(c.id)
            combined.append(c)

    db.close()
    return combined


def search_documents(question: str, top_k: int = 5, candidate_pool: int = 50):
    from generate import expand_query
    queries = expand_query(question)

    all_pool = []
    seen_ids = set()
    for q in queries:
        for chunk in search_chunk(q, top_k=candidate_pool):
            if chunk.id not in seen_ids:
                seen_ids.add(chunk.id)
                all_pool.append(chunk)

    Finals = []
    for chunk in all_pool:
        doc_id = chunk.document_id
        if doc_id not in Finals and len(Finals) < top_k:
            Finals.append(doc_id)

    dictofchunk = {}
    for doc_id in Finals:
        dictofchunk[doc_id] = search_chunk_in_document(question, doc_id, top_k=5)
    return dictofchunk