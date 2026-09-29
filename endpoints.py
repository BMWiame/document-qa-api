import os
from fastapi import FastAPI, UploadFile, File, HTTPException
from models import Document,Chunk
from database import SessionLocal
from tasks import process_document_task
from embed import get_embedding
from pydantic import BaseModel,Field
from search import search_documents
from generate import generate_answer

app=FastAPI()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.get("/documents/")
def list_documents():
    db=SessionLocal()
    documents=db.query(Document).all()
    db.close()
    return [{"id": d.id, "filename": d.filename, "status": d.status} for d in documents]
@app.post("/documents/upload")
async def upload_doc(file: UploadFile = File(...)):
    db=SessionLocal()
    file_path=os.path.join(UPLOAD_DIR,file.filename)
    with open(file_path,"wb") as f:
        f.write(await file.read())
    doc = Document(filename=file.filename, status="pending")
    db.add(doc)
    db.commit()
    db.refresh(doc)
    db.close()
    process_document_task.delay(doc.id, file_path)
    return {"id": doc.id, "filename": doc.filename}
@app.delete("/documents/{doc_id}")
def delete_documents(doc_id:int):
    db=SessionLocal()
    doc=db.query(Document).filter(Document.id==doc_id).first()
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")
    db.delete(doc)
    db.commit()
    db.close()
    return {"details":"Document has been deleted"}

@app.get("/documents/{document_id}/status")
def get_status(document_id: int):
    db = SessionLocal()
    doc = db.query(Document).filter(Document.id == document_id).first()
    db.close()
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"id": doc.id, "status": doc.status}

class Question(BaseModel):
    question:str=Field(title="What do you want to know?")



@app.post("/ask")
def asking(question: Question):
    results = search_documents(question.question)
    all_chunks = [chunk.content for chunks in results.values() for chunk in chunks]
    answer=generate_answer(question.question,all_chunks)
    return {"answer": answer}
    
