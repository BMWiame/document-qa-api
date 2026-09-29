from dotenv import  load_dotenv
import os
import google.generativeai as genai
load_dotenv()
api_key= os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=api_key)

model = genai.GenerativeModel("gemini-flash-latest")


def generate_answer(question: str, chunks: list[str]) -> str:
    sources_text = "\n\n".join(f"Source {i+1}: {chunk}" for i, chunk in enumerate(chunks))

    prompt = f"""Answer the question using only the information in the sources below.
If the answer isn't in the sources, say you don't know.

{sources_text}

Question: {question}"""

    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        if "RESOURCE_EXHAUSTED" in str(e) or "429" in str(e):
            return "Daily API quota reached. Try again after the quota resets."
        return f"Error generating answer: {e}"

def expand_query(question: str) -> list[str]:
    prompt = f"""Generate 3 alternative ways to phrase this question, using different words and specific terms that might appear in a document containing the answer. Return only the 3 alternatives, one per line, no numbering.

Question: {question}"""
    try:
        response = model.generate_content(prompt)
        alternatives = [line.strip() for line in response.text.split("\n") if line.strip()]
        return [question] + alternatives
    except Exception:
        return [question]