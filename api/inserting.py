from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Dict
import re

router = APIRouter()

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
    rest = sentences[:insert_index] + sentences[insert_index + 1:]
    paragraph = []
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
        label_map = {p: CIRCLED[i] for i, p in enumerate(insertion_points)}
        if insert_index in insertion_points:
            answer = CIRCLED[insertion_points.index(insert_index)]
        for i in range(len(rest) + 1):
            if i in label_map:
                paragraph.append(label_map[i])
            if i < len(rest):
                paragraph.append(rest[i])

    text = (
        "글의 흐름으로 보아, 주어진 문장이 들어가기에 가장 적절한 곳은?\n\n"
        + given + "\n\n" + " ".join(paragraph)
    )
    return {"text": text, "answer": answer}

def generate_all_insertion_problems(text: str) -> List[Dict[str, str]]:
    sentences = split_paragraph_into_sentences(text)
    if len(sentences) < 5:
        return [{"error": "문장 수가 5개 이상이어야 합니다."}]
    
    eligible = list(range(5)) if len(sentences) == 5 else [len(sentences) - 6 + i for i in range(5)]
    return [
        {
            "number": i + 1,
            "problem": generate_insertion_problem(sentences, idx)["text"],
            "answer": generate_insertion_problem(sentences, idx)["answer"],
        }
        for i, idx in enumerate(eligible)
    ]

@router.post("/inserting")
def handle_inserting(payload: TextPayload):
    return generate_all_insertion_problems(payload.text)
