# Document Q&A API

A backend service that lets you upload documents (PDF/TXT) and ask natural-language questions about their content, using retrieval-augmented generation (RAG).

## How it works

1. **Upload** — a document is saved and a background job is queued (Celery + Redis) so the API responds immediately instead of blocking on processing.
2. **Extract & chunk** — text is pulled from the file (`pypdf`), split into sentences (`nltk`), and grouped into overlapping chunks (last few sentences of one chunk carry into the next) so a fact sitting near a chunk boundary isn't isolated from its surrounding context.
3. **Embed** — each chunk, prefixed with its source filename for identity context, is converted into a 384-dimension vector using a multilingual sentence-transformers model, and stored in Postgres via `pgvector`.
4. **Retrieve** — a question is:
   - expanded by an LLM into a few alternative phrasings, to catch cases where the answer uses different vocabulary than the question,
   - embedded and matched against stored chunks by cosine similarity,
   - combined with a direct keyword search, so literal terms (e.g. acronyms) are never missed regardless of embedding rank.
5. **Aggregate** — results are grouped by document, not just raw chunk rank, so one large document can't crowd out a smaller but more relevant one in the results.
6. **Generate** — the top matching chunks, across the most relevant documents, are passed to an LLM (Gemini) with instructions to answer only from that context, and to say so honestly if the answer isn't there — rather than guessing.

## Tech stack

- **FastAPI** — REST API
- **PostgreSQL + pgvector** — storage and vector similarity search
- **SQLAlchemy** — ORM
- **Celery + Redis** — background document processing
- **sentence-transformers** (`paraphrase-multilingual-MiniLM-L12-v2`) — multilingual embeddings
- **Google Gemini API** — query expansion and answer generation
- **pypdf / nltk** — text extraction and sentence splitting

## Endpoints

| Method | Path | Description |
|---|---|---|
| POST | `/documents/upload` | Upload a PDF/TXT file |
| GET | `/documents/` | List all documents and their status |
| GET | `/documents/{id}/status` | Check processing status (pending/processing/done) |
| DELETE | `/documents/{id}` | Delete a document and its chunks |
| POST | `/ask` | Ask a question across all uploaded documents |

## Setup

```bash
python -m venv venv
venv\Scripts\Activate.ps1   # Windows
pip install -r requirements.txt

# Postgres with pgvector
docker run --name pgqa -e POSTGRES_PASSWORD=rain -e POSTGRES_DB=docqa -p 5432:5432 -d pgvector/pgvector:pg16
docker exec -it pgqa psql -U postgres -d docqa -c "CREATE EXTENSION IF NOT EXISTS vector;"

# Redis
docker run --name redis-qa -p 6379:6379 -d redis:7-alpine

# Create tables
python create_tables.py

# .env file (create manually)
GEMINI_API_KEY=your_key_here
```

Run (three separate terminals):
```bash
uvicorn endpoints:app --reload
celery -A celery_app worker --loglevel=info --pool=solo
```

If Gemini renames its models again (it has happened once already), run `python list_models.py` to see which model names your API key currently supports.

## Evaluation

`daily_test.py` runs a small daily batch of real questions from the [QASPER](https://huggingface.co/datasets/allenai/qasper) academic-paper QA benchmark against the live API, logs each question/answer/reference to `daily_test_log.txt`, and applies a rough automatic verdict (exact-phrase match against the reference) for a first pass — genuine review still requires reading flagged entries manually.

Sample results against real, previously-unseen papers:
- *"which multilingual approaches do they compare with?"* → correctly identified the cited baseline (BIBREF19)
- *"what are the pivot-based baselines?"* → correctly distinguished "pivoting" vs "pivot-synthetic," matching the paper's own definitions
- *"which datasets did they experiment with?"* → exact match: "Europarl and MultiUN"
- *"what NER models were evaluated?"* → correctly listed all three models with their distinguishing techniques

`QUESTIONS_PER_RUN` is set low (1) because query expansion doubles the LLM calls per question (one to expand, one to answer), and Gemini's free tier caps at 20 requests/day.

## Design decisions & known limitations

- **Overlapping chunks**: reduces (but doesn't eliminate) the chance that a fact — like a definition — gets split across a chunk boundary and missed by both halves.
- **Hybrid search**: combines semantic similarity with exact keyword matching, since embeddings alone can under-rank literal terms (e.g. acronyms) or over-rank generic text that happens to share vocabulary with the question (e.g. a table of contents).
- **Query expansion**: an LLM generates alternative phrasings of the question before retrieval, to catch cases where the answer's wording shares little vocabulary with the question itself (e.g. asking for a "source" when the actual answer is a specific website name never mentioned in the question). This roughly doubles API cost per question — a deliberate recall-vs-cost tradeoff, tunable based on available quota.
- **Contextual chunk embedding**: each chunk is embedded with its source filename prepended, so identity-related questions ("who does this document belong to?") have a better chance of connecting scattered content back to its source.
- **Document-level aggregation**: results are ranked by document (using each document's best-matching chunk), not by raw chunk count, so a large document (hundreds of chunks) can't statistically dominate a small one (a few chunks) purely by volume.
- **Grounded generation**: the model is explicitly instructed to answer only from retrieved context and decline rather than guess — validated against QASPER, where it correctly said "I don't know" on a question whose answer genuinely wasn't stated in the source (rather than inventing one).
- **Not fully solved**: retrieval can still miss an answer when its wording is both distant from the question *and* far from any chunk boundary — query expansion and overlap mitigate this but don't guarantee recall. A production system would likely add reranking (a second, more precise model scoring the top candidates) to close this gap further.