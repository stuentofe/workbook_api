import re
import spacy
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Dict

nlp = spacy.load("en_core_web_sm")

router = APIRouter()

class TextPayload(BaseModel):
    text: str

def split_paragraph_into_sentences(text: str) -> List[str]:
    text = text.replace("\r", " ").replace("\n", " ")
    return re.findall(r"[^.!?]+[.!?]+", text)

def generate_verbrewrite(sentences: List[Dict[str, str]]) -> Dict[str, str]:
    problems = []
    answers = []

    for item in sentences:
        doc = nlp(item["text"])
        new_tokens = []
        original_verbs = []
        i = 0

        while i < len(doc):
            tok = doc[i]

            if tok.lemma_ == "be" and tok.pos_ == "AUX":
                next_tok = doc[i + 1] if i + 1 < len(doc) else None
                if next_tok and next_tok.tag_ in ("VBN", "VBG"):
                    new_tokens.append(f"({next_tok.lemma_})")
                    original_verbs.append(f"{tok.text} {next_tok.text}")
                    i += 2
                    continue
                else:
                    new_tokens.append(f"({tok.lemma_})")
                    original_verbs.append(tok.text)
                    i += 1
                    continue

            elif tok.pos_ == "VERB":
                new_tokens.append(f"({tok.lemma_})")
                original_verbs.append(tok.text)
            else:
                new_tokens.append(tok.text)

            i += 1

        problems.append(f"{item['num']}. {' '.join(new_tokens)}")
        answers.append(f"{item['num']}. {', '.join(original_verbs)}")

    return {
        "problem": "\n\n\n\n".join(problems),
        "answer": "\n".join(answers)
    }

@router.post("/verbrewrite")
async def verbrewrite_api(payload: TextPayload):
    raw_sentences = split_paragraph_into_sentences(payload.text)
    data = [{"num": i + 1, "text": s.strip()} for i, s in enumerate(raw_sentences)]
    if not data:
        return {"error": "문장을 찾을 수 없습니다."}
    return generate_verbrewrite(data)
