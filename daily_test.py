import json
import os
import time
from datetime import datetime
import requests
from datasets import load_dataset

STATE_FILE = "daily_test_state.json"
LOG_FILE = "daily_test_log.txt"
QUESTIONS_PER_RUN = 4
API_URL = "http://127.0.0.1:8000"


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return {"paper_index": 0, "question_index": 0, "uploaded_doc_id": None}


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)


def paper_to_text(paper):
    text = ""
    for section, paragraphs in zip(paper["full_text"]["section_name"], paper["full_text"]["paragraphs"]):
        text += f"\n\n{section}\n" + "\n".join(paragraphs)
    return text


def upload_paper(paper):
    text = paper_to_text(paper)
    tmp_path = "daily_test_paper.txt"
    with open(tmp_path, "w", encoding="utf-8") as f:
        f.write(text)
    with open(tmp_path, "rb") as f:
        response = requests.post(f"{API_URL}/documents/upload", files={"file": f})
    doc_id = response.json()["id"]

    while True:
        status = requests.get(f"{API_URL}/documents/{doc_id}/status").json()["status"]
        if status == "done":
            break
        time.sleep(3)
    return doc_id


def check_verdict(your_answer, reference_answers):
    your_answer_lower = your_answer.lower()
    for ref in reference_answers:
        candidates = ref.get("extractive_spans", []) + ([ref["free_form_answer"]] if ref.get("free_form_answer") else [])
        for c in candidates:
            if c and c.lower() in your_answer_lower:
                return f"LIKELY CORRECT (matched: '{c}')"
    return "NEEDS REVIEW (no direct match found — read manually)"


def main():
    dataset = load_dataset("allenai/qasper")
    state = load_state()
    paper = dataset["validation"][state["paper_index"]]

    if state["uploaded_doc_id"] is None:
        print(f"Uploading new paper: {paper['title']}")
        state["uploaded_doc_id"] = upload_paper(paper)
        save_state(state)

    questions = paper["qas"]["question"]
    answer_groups = paper["qas"]["answers"]
    start = state["question_index"]
    end = min(start + QUESTIONS_PER_RUN, len(questions))

    with open(LOG_FILE, "a", encoding="utf-8") as log:
        log.write(f"\n===== Run: {datetime.now().isoformat()} =====\n")
        log.write(f"Paper: {paper['title']}\n\n")

        for i in range(start, end):
            question = questions[i]
            reference = answer_groups[i]["answer"]

            try:
                response = requests.post(f"{API_URL}/ask", json={"question": question})
                your_answer = response.json().get("answer", response.text)
            except Exception as e:
                your_answer = f"ERROR: {e}"

            verdict = check_verdict(your_answer, reference)

            log.write(f"Q: {question}\nYour answer: {your_answer}\nReference: {reference}\nVerdict: {verdict}\n---\n")
            print(f"Q: {question}\nVerdict: {verdict}\n---")

            time.sleep(10)

    state["question_index"] = end
    if state["question_index"] >= len(questions):
        state["paper_index"] += 1
        state["question_index"] = 0
        state["uploaded_doc_id"] = None
    save_state(state)

    print(f"\nDone. Logged to {LOG_FILE}. Resumes tomorrow at paper {state['paper_index']}, question {state['question_index']}.")


if __name__ == "__main__":
    main()