from extract import extract_chunks
from models import Chunk
from database import SessionLocal
from embed import get_embedding

from models import Document, Chunk

def processing_chunks(document_id: int, file_path: str):
    db = SessionLocal()
    doc = db.query(Document).filter(Document.id == document_id).first()
    filename = doc.filename

    for chunk in extract_chunks(file_path):
        text_for_embedding = f"Document: {filename}. {chunk}"
        embedding = get_embedding(text_for_embedding)
        ch = Chunk(content=chunk, document_id=document_id, embedding=embedding)
        db.add(ch)
    db.commit()
    db.close()