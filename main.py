import re
import random
from typing import List, Dict
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class TextPayload(BaseModel):
    text: str

CIRCLED = ["①", "②", "③", "④", "⑤"]


def split_paragraph_into_sentences(text: str) -> List[str]:
    text = text.replace("\r\n", " ").replace("\n", " ")
    matches = re.findall(r"[^.!?]+[.!?]+", text)
    return [m.strip() for m in matches] if matches else []


def generate_insertion_problem(sentences: List[str], insert_index: int) -> Dict[str, str]:
    n = len(sentences)
    given = sentences[insert_index]
    rest = sentences[:insert_index] + sentences[insert_index + 1 :]
    paragraph: List[str] = []
    answer = None

    if n == 5:
        for i in range(len(rest) + 1):
            if i < 5:
                paragraph.append(CIRCLED[i])
            if i < len(rest):
                paragraph.append(rest[i])
        answer = CIRCLED[insert_index]
    else:
        base = n - 6
        insertion_points = [base + i for i in range(5)]
        label_map = {p_idx: CIRCLED[i] for i, p_idx in enumerate(insertion_points)}
        p_before = insert_index
        if p_before in insertion_points:
            answer = CIRCLED[insertion_points.index(p_before)]
        for i in range(len(rest) + 1):
            if i in label_map:
                paragraph.append(label_map[i])
            if i < len(rest):
                paragraph.append(rest[i])

    text = (
        "글의 흐름으로 보아, 주어진 문장이 들어가기에 가장 적절한 곳은?\n\n"
        + given
        + "\n\n"
        + " ".join(paragraph)
    )
    return {"text": text, "answer": answer}


def generate_all_insertion_problems(text: str) -> List[Dict[str, str]]:
    sentences = split_paragraph_into_sentences(text)
    n = len(sentences)
    if n < 5:
        return [{"error": "문장 수가 5개 이상이어야 합니다."}]

    eligible = [i for i in range(5)] if n == 5 else [n - 6 + i for i in range(5)]
    results = []
    for i, idx in enumerate(eligible):
        prob = generate_insertion_problem(sentences, idx)
        results.append({"number": i + 1, "problem": prob["text"], "answer": prob["answer"]})
    return results


def get_valid_4_chunk_combinations(n: int) -> List[List[int]]:
    result: List[List[int]] = []

    def dfs(current: List[int], total: int) -> None:
        if len(current) == 4 and total == n:
            result.append(current[:])
            return
        if len(current) >= 4 or total >= n:
            return
        max_chunk_size = 3 if n >= 9 else 2
        for i in range(1, max_chunk_size + 1):
            dfs(current + [i], total + i)

    dfs([], 0)
    return result


def chunk_sentences(sentences: List[str], sizes: List[int]) -> List[str]:
    result = []
    idx = 0
    for size in sizes:
        result.append(" ".join(sentences[idx : idx + size]))
        idx += size
    return result


def generate_single_order_question(o: str, p: str, q: str, r: str) -> Dict[str, str]:
    perms = [
        ["a", "c", "b"],
        ["b", "a", "c"],
        ["b", "c", "a"],
        ["c", "a", "b"],
        ["c", "b", "a"],
    ]
    la, lb, lc = random.choice(perms)
    labels = {la: p, lb: q, lc: r}
    reverse = {p: la, q: lb, r: lc}

    lines = []
    lines.append("주어진 글 다음에 이어질 글의 흐름으로 가장 적절한 것은?\n")
    lines.append(o + "\n")
    lines.append(f"(A) {labels['a']}")
    lines.append(f"(B) {labels['b']}")
    lines.append(f"(C) {labels['c']}\n")
    lines.append("① (A) - (C) - (B)")
    lines.append("② (B) - (A) - (C)")
    lines.append("③ (B) - (C) - (A)")
    lines.append("④ (C) - (A) - (B)")
    lines.append("⑤ (C) - (B) - (A)")
    question_text = "\n".join(lines)

    correct_label = reverse[p] + reverse[q] + reverse[r]
    answer_key = {"acb": 1, "bac": 2, "bca": 3, "cab": 4, "cba": 5}
    answer = CIRCLED[answer_key[correct_label] - 1]

    return {"question": question_text, "answer": answer}


def generate_all_order_questions(sentences: List[str]) -> List[Dict[str, str]]:
    if len(sentences) < 4:
        return [{"error": "문장 수 부족"}]

    results = []
    combinations = get_valid_4_chunk_combinations(len(sentences))
    for i, sizes in enumerate(combinations):
        o, p, q, r = chunk_sentences(sentences, sizes)
        qa = generate_single_order_question(o, p, q, r)
        results.append({"number": i + 1, "problem": qa["question"], "answer": qa["answer"]})
    return results


@app.post("/inserting")
async def inserting(payload: TextPayload):
    return generate_all_insertion_problems(payload.text)


@app.post("/ordering")
async def ordering(payload: TextPayload):
    sentences = split_paragraph_into_sentences(payload.text)
    return generate_all_order_questions(sentences)

