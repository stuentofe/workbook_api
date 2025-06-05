from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Dict
import re
import random

router = APIRouter()

class TextPayload(BaseModel):
    text: str

CIRCLED = ["①", "②", "③", "④", "⑤"]

def split_paragraph_into_sentences(text: str) -> List[str]:
    text = text.replace("\r\n", " ").replace("\n", " ")
    matches = re.findall(r"[^.!?]+[.!?]+", text)
    return [m.strip() for m in matches] if matches else []

def get_valid_4_chunk_combinations(n: int) -> List[List[int]]:
    result = []

    def dfs(current, total):
        if len(current) == 4 and total == n:
            result.append(current[:])
            return
        if len(current) >= 4 or total >= n:
            return
        max_chunk = 3 if n >= 9 else 2
        for i in range(1, max_chunk + 1):
            dfs(current + [i], total + i)

    dfs([], 0)
    return result

def chunk_sentences(sentences: List[str], sizes: List[int]) -> List[str]:
    result, idx = [], 0
    for size in sizes:
        result.append(" ".join(sentences[idx:idx + size]))
        idx += size
    return result

def generate_single_order_question(o, p, q, r) -> Dict[str, str]:
    perms = [
        ["a", "c", "b"], ["b", "a", "c"], ["b", "c", "a"],
        ["c", "a", "b"], ["c", "b", "a"]
    ]
    [la, lb, lc] = random.choice(perms)
    labels = {la: p, lb: q, lc: r}
    reverse = {p: la, q: lb, r: lc}

    lines = [
        "주어진 글 다음에 이어질 글의 흐름으로 가장 적절한 것은?\n",
        o + "\n",
        f"(A) {labels['a']}",
        f"(B) {labels['b']}",
        f"(C) {labels['c']}\n",
        "① (A) - (C) - (B)",
        "② (B) - (A) - (C)",
        "③ (B) - (C) - (A)",
        "④ (C) - (A) - (B)",
        "⑤ (C) - (B) - (A)"
    ]

    correct = reverse[p] + reverse[q] + reverse[r]
    answer_map = {"acb": 1, "bac": 2, "bca": 3, "cab": 4, "cba": 5}
    answer = CIRCLED[answer_map[correct] - 1]
    return {"question": "\n".join(lines), "answer": answer}

def generate_all_order_questions(sentences: List[str]) -> List[Dict[str, str]]:
    if len(sentences) < 4:
        return [{"error": "문장 수 부족"}]

    results = []
    combinations = get_valid_4_chunk_combinations(len(sentences))
    for i, sizes in enumerate(combinations):
        o, p, q, r = chunk_sentences(sentences, sizes)
        qna = generate_single_order_question(o, p, q, r)
        results.append({
            "number": i + 1,
            "problem": qna["question"],
            "answer": qna["answer"]
        })
    return results

@router.post("/ordering")
def handle_ordering(payload: TextPayload):
    sentences = split_paragraph_into_sentences(payload.text)
    return generate_all_order_questions(sentences)
