from sentence_transformers import SentenceTransformer
model=SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
def get_embedding(text):
    embedding=model.encode(text)
    return embedding.tolist()

