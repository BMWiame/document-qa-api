import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

# Initialize the Gemini client (automatically reads GEMINI_API_KEY from environment)
_client = None

def get_client():
    global _client
    if _client is None:
        _client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    return _client

# Use Gemini 2.5 Flash for high throughput, low latency, and free-tier access
MODEL_NAME = "gemini-3.8-flash"


def generate_answer(question: str, chunks: list[str]) -> str:
    sources_text = "\n\n".join(
        f"--- CHUNK {i+1} ---\n{chunk}" for i, chunk in enumerate(chunks)
    )

    prompt = f"""You are a strict factual document search engine. 

Rules:
1. Answer the question relying ONLY on the clear facts directly mentioned in the Context below.
2. Do NOT use any external knowledge, general definitions, or pre-trained memory.
3. Do NOT extrapolate, speculate, or infer beyond what is explicitly stated.
4. If the exact answer cannot be directly extracted from the provided Context, reply with exact text: "I don't know."

Context:
{sources_text}

Question: {question}
Answer:"""

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.0,  # Forces strict, non-creative context extraction
            ),
        )
        return response.text.strip() if response.text else "I don't know."
    except Exception as e:
        return f"Error: {e}"


def expand_query(question: str) -> list[str]:
    prompt = f"""Generate 3 alternative ways to phrase this question, using different words and specific terms that might appear in a document containing the answer. Return only the 3 alternatives, one per line, no numbering.

Question: {question}"""

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.7,
            ),
        )
        raw_text = response.text or ""
        alternatives = [
            line.strip() for line in raw_text.split("\n") if line.strip()
        ]
        return [question] + alternatives
    except Exception:
        return [question]