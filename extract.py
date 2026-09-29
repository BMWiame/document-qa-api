import os
from pypdf import PdfReader
from nltk.tokenize import sent_tokenize

def extract_text(file_path: str) -> str:
    typefile = os.path.splitext(file_path)[1].lower()
    if typefile == ".pdf":
        reader = PdfReader(file_path)
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
    elif typefile == ".txt":
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()

    return " ".join(text.split())

def sentence_splitter(file_path: str):
    full_text = extract_text(file_path)
    return sent_tokenize(full_text)

def extract_chunks(file_path: str, overlap_sentences: int = 4):
    sentences = sentence_splitter(file_path)
    chunk = ""
    chunks = []
    current_sentences = []

    for sentence in sentences:
        if len(chunk) + len(sentence) <= 800:
            chunk += " " + sentence
            current_sentences.append(sentence)
        else:
            chunks.append(chunk.strip())
            overlap = current_sentences[-overlap_sentences:]
            chunk = " ".join(overlap) + " " + sentence
            current_sentences = overlap + [sentence]

    if chunk:
        chunks.append(chunk.strip())
    return chunks

if __name__ == "__main__":
    chunks = extract_chunks("uploads/os-module-guide.pdf")
    print(f"Number of chunks: {len(chunks)}")
    print(chunks[0])
    print(chunks[1])