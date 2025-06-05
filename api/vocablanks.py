from fastapi import APIRouter
from pydantic import BaseModel
from typing import List
import spacy

nlp = spacy.load("en_core_web_sm")

router = APIRouter()

class SentenceItem(BaseModel):
    num: int
    text: str

class SentencesPayload(BaseModel):
    sentences: List[SentenceItem]

@router.post("/vocablanks")
def vocablanks_api(payload: SentencesPayload):
    return generate_vocablanks(payload.sentences)

def generate_vocablanks(sentences):
    blanks = []
    answers = []

    for item in sentences:
        sent = item.text
        doc = nlp(sent)

        total_words = len([t for t in doc if not t.is_punct and not t.is_space])
        num_blanks = min(5, max(1, total_words // 5))

        candidates = []

        for chunk in doc.noun_chunks:
            tokens = [t for t in chunk if t.pos_ in {"NOUN", "PROPN", "ADJ"}]
            if tokens:
                text = " ".join(t.text for t in tokens)
                candidates.append((text, chunk.start_char, chunk.end_char, chunk.start))

        for t in doc:
            if t.pos_ in {"NOUN", "VERB", "ADJ", "ADV", "PROPN"} and not t.is_stop and not t.is_punct:
                candidates.append((t.text, t.idx, t.idx + len(t.text), t.i))

        seen_ranges = set()
        clean_candidates = []
        for text, start, end, idx in sorted(candidates, key=lambda x: x[3]):
            if any((s <= start < e) or (s < end <= e) for s, e in seen_ranges):
                continue
            seen_ranges.add((start, end))
            clean_candidates.append((text, start, end, idx))

        if not clean_candidates:
            blanks.append(f"{item.num}. {sent}")
            answers.append(f"{item.num}. (no blanks)")
            continue

        spacing = len(doc) / num_blanks
        targets = [int(spacing * i + spacing / 2) for i in range(num_blanks)]

        selected = []
        used = set()
        for target_idx in targets:
            closest = min(
                (c for c in clean_candidates if c[3] not in used),
                key=lambda x: abs(x[3] - target_idx),
                default=None
            )
            if closest:
                selected.append(closest)
                used.add(closest[3])

        answers.append(f"{item.num}. {', '.join(x[0] for x in selected)}")

        modified = sent
        offset = 0
        for phrase, start, end, _ in selected:
            blank_phrase = " ".join(["____"] * len(phrase.split()))
            modified = modified[:start - offset] + blank_phrase + modified[end - offset:]
            offset += (end - start) - len(blank_phrase)

        blanks.append(f"{item.num}. {modified.strip()}")

    return {
        "problem": "\n\n\n\n".join(blanks),
        "answer": "\n".join(answers)
    }
