from celery_app import celery_app
from processing import processing_chunks
from database import SessionLocal
from models import Document
@celery_app.task(bind=True,max_retries=3,default_retry_delay=10)
def process_document_task(self,document_id:int, file_path:str):
    try:
        db=SessionLocal()
        doc=db.query(Document).filter(Document.id==document_id).first()
        doc.status="processing"
        db.commit()
        processing_chunks(document_id,file_path)
        doc.status="done"
        db.commit()
        
    except Exception as exc:
        raise self.retry(exc=exc)
    finally:
        db.close()