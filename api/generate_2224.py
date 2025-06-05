# 전체 generate_2224.py FastAPI 라우터 구현
# 이 코드는 기존 JavaScript 기반 Gemini API 호출 로직을 Python으로 완전히 이식한 버전입니다.
# 텍스트 문제 생성 (요지, 주제, 제목)을 지원합니다.

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Literal, Dict
import requests
import os
import re

router = APIRouter()

class GeneratePayload(BaseModel):
    type: Literal["gist", "topic", "title"]
    text: str

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-pro:generateContent"

number_labels = ['①', '②', '③', '④', '⑤']

def fill_template(template: str, values: Dict[str, str]) -> str:
    for k, v in values.items():
        template = template.replace(f"{{{{{k}}}}}", v)
    return template

def call_gemini(prompt: str) -> str:
    headers = {"Content-Type": "application/json"}
    body = {
        "contents": [
            {"role": "user", "parts": [{"text": "Never respond conversationally."}]},
            {"role": "user", "parts": [{"text": prompt}]}
        ],
        "generationConfig": {
            "temperature": 0.7
        },
        "safetySettings": [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
        ]
    }

    res = requests.post(f"{GEMINI_API_URL}?key={GEMINI_API_KEY}", json=body, headers=headers)
    res.raise_for_status()
    data = res.json()
    return data['candidates'][0]['content']['parts'][0]['text'].strip()

def extract_passage_and_star(passage: str):
    match = re.match(r"^(.*?)(\*.+)$", passage.strip(), flags=re.DOTALL)
    if match:
        return match.group(1).strip() + "\n" + match.group(2).strip()
    return passage.strip()

def generate_problem_series(base_key: str, explanation_key: str, passage: str):
    full_passage = extract_passage_and_star(passage)

    c = call_gemini(fill_template(inlinePrompts[f"{base_key}c"], {"p": full_passage}))
    w = call_gemini(fill_template(inlinePrompts[f"{base_key}w"], {"p": full_passage, "c": c}))
    x = call_gemini(fill_template(inlinePrompts[f"{base_key}x"], {"p": full_passage, "c": c, "w": w}))
    y = call_gemini(fill_template(inlinePrompts[f"{base_key}y"], {"p": full_passage, "c": c, "w": w, "x": x}))
    z = call_gemini(fill_template(inlinePrompts[f"{base_key}z"], {"p": full_passage, "c": c, "w": w, "x": x, "y": y}))

    options = [
        {"key": "c", "value": c},
        {"key": "w", "value": w},
        {"key": "x", "value": x},
        {"key": "y", "value": y},
        {"key": "z", "value": z},
    ]

    sorted_options = sorted(options, key=lambda x: len(x["value"]))
    for i, opt in enumerate(sorted_options):
        opt["number"] = number_labels[i]
        opt["text"] = f"{number_labels[i]} {opt['value']}"

    question_text = f"{full_passage}\n\n" + "\n".join(opt["text"] for opt in sorted_options)
    answer = next((opt["number"] for opt in sorted_options if opt["key"] == "c"), None)
    explanation = call_gemini(fill_template(inlinePrompts[explanation_key], {"p": question_text}))

    return {
        "problem": question_text,
        "answer": answer,
        "explanation": explanation
    }

@router.post("/generate")
def generate_2224_problem(payload: GeneratePayload):
    mapping = {
        "gist": ("const", "conste"),
        "topic": ("const", "constee"),
        "title": ("const", "consteee")
    }
    base_key, explanation_key = mapping[payload.type]
    return generate_problem_series(base_key, explanation_key, payload.text)

# 아래 prompt 템플릿은 외부에서 관리하는 게 좋지만, 여기에 포함합니다.
inlinePrompts = {
     "constc": """영어 지문을 읽고 글의 요지를 파악해서 고르는 객관식 문제를 만들려고 한다. 지금 현재 준비된 것은 다음과 같다.

======================
다음 글의 요지로 가장 적절한 것은?
{{p}}

①
②
③
④
⑤
======================

지금 당장 필요한 것은, 정답 선택지를 만드는 것이다. 정답 선택지는 지문의 요지를 담아내는 '~다' 체의 25자 이내의 한국어 문장이어야 한다. 설명 없이, 네가 만든 정답 선택지를 출력하라.""",

    "constw": """영어 지문을 읽고 글의 요지를 파악해서 고르는 이지선다형 객관식 문제를 만들려고 한다. 지금 현재 준비된 것은 다음과 같다.

======================
다음 글의 요지로 가장 적절한 것은?
{{p}}

① {{c}}
② 
======================

지금 당장 필요한 것은, 오답 선택지를 채우는 것이다. [중요!] 정답 선택지와 길이만 유사할 뿐 충분히 달라야 한다. (문장 구조나 단어를 흉내내는 것 절대 금지)
오답 선택지를 만들기 위해 영어지문에 사용된 어휘를 사용할 수는 있지만, 영어지문 내용과 부분적으로 일치하는 것이 오답이 되어서는 안된다. (복수정답 방지)
다른 설명 없이, 네가 만든 오답 문장을(번호 제외) 출력하라.""",

    "constx": """영어 지문을 읽고 글의 요지를 파악해서 고르는 삼지선다형 객관식 문제를 만들려고 한다. 지금 현재 준비된 것은 다음과 같다.

======================
다음 글의 요지로 가장 적절한 것은?
{{p}}

① {{c}}
② {{w}}
③
======================

지금 당장 필요한 것은, 딱 하나 남은 오답 선택지를 채우는 것이다. [중요!] 다른 선택지와 충분히 달라야 한다. (문장 구조나 단어를 흉내내는 것 절대 금지) 
오답 선택지를 만들기 위해 영어지문에 사용된 어휘를 사용할 수는 있지만, 영어지문 내용과 부분적으로 일치하는 것이 오답이 되어서는 안된다. (복수정답 방지)
다른 설명 없이, 네가 만든 남은 하나의 오답 문장을(번호 제외)  출력하라.""",

    "consty": """영어 지문을 읽고 글의 요지를 파악해서 고르는 사지선다형 객관식 문제를 만들려고 한다. 지금 현재 준비된 것은 다음과 같다.

======================
다음 글의 요지로 가장 적절한 것은?
{{p}}

① {{c}}
② {{w}}
③ {{x}}
④
======================

지금 당장 필요한 것은, 딱 하나 남은 오답 선택지를 채우는 것이다. [중요!] 다른 선택지와 충분히 달라야 한다. (문장 구조나 단어를 흉내내는 것 절대 금지) 
오답 선택지를 만들기 위해 영어지문에 사용된 어휘를 사용할 수는 있지만, 영어지문 내용과 부분적으로 일치하는 것이 오답이 되어서는 안된다. (복수정답 방지)
다른 설명 없이, 네가 만든 남은 하나의 오답 문장을(번호 제외)  출력하라.""",

    "constz": """영어 지문을 읽고 글의 요지를 파악해서 고르는 오지선다형 객관식 문제를 만들려고 한다. 지금 현재 준비된 것은 다음과 같다.

======================
다음 글의 요지로 가장 적절한 것은?
{{p}}

① {{c}}
② {{w}}
③ {{x}}
④ {{y}}
⑤
======================

지금 당장 필요한 것은, 딱 하나 남은 오답 선택지를 채우는 것이다. [중요!] 다른 선택지와 충분히 달라야 한다. (문장 구조나 단어를 흉내내는 것 절대 금지) 
오답 선택지를 만들기 위해 영어지문에 사용된 어휘를 사용할 수는 있지만, 영어지문 내용과 부분적으로 일치하는 것이 오답이 되어서는 안된다. (복수정답 방지)
다른 설명 없이, 네가 만든 남은 하나의 오답 문장을(번호 제외)  출력하라.""",

    "conste": """다음 영어지문의 요지를 파악하는 문제의 해설을 작성해야 한다. 다른 설명은 하지말고 아래 예시의 포맷에 맞추어 주어진 문제를 풀고 그에 대한 해설을 작성해 출력하라.

===포맷===
정답: 번호
(정답의 근거가 될 수 있는 내용)라는 내용의 글이다. 이러한 글의 요지는, 문장 "(지문에 사용된 영어 문장)" (인용 문장에 대한 한국어해석)에서 가장 명시적으로 드러난다. 따라서 글의 요지는 (정답번호)가 가장 적절하다.
===예시===
정답: ④
정체성은 행동의 반영이며, 믿는 정체성에 따라 행동한다는 내용의 글이다. 이러한 글의 요지는, 문장 "Your behaviors are usually a reflection of your identity." (당신의 행동은 대개 당신의 정체성을 반영하는 것이다.)에서 가장 명시적으로 드러난다. 따라서, 글의 요지는 ④가 가장 적절하다.
=========

===네가 해설을 만들어야할 문제===
{{p}}""",

    "constcc": """영어 지문을 읽고 글의 주제를 파악해서 고르는 객관식 문제를 만들려고 한다. 지금 현재 준비된 것은 다음과 같다.

======================
다음 글의 주제로 가장 적절한 것은?
{{p}}

①
②
③
④
⑤
======================

지금 당장 필요한 것은, 정답 선택지를 만드는 것이다. 정답 선택지는 지문의 요지를 담아내는 영어 명사구여야 한다. 다른 설명 없이, 네가 만든 정답 선택지 하나의 영어 명사구만을(번호 제외) 출력하라. 
문장이 아니므로 첫단어도 소문자로 써라.

===예시===
shift in the work-time paradigm brought about by industrialization
effects of standardizing production procedures on labor markets
influence of industrialization on the machine-human relationship
efficient ways to increase the value of time in the Industrial Age
problems that excessive work hours have caused for laborers
=========""",

    "constww": """영어 지문을 읽고 글의 주제를 파악해서 고르는 이지선다형 객관식 문제를 만들려고 한다. 지금 현재 준비된 것은 다음과 같다.

======================
다음 글의 주제로 가장 적절한 것은?
{{p}}

① {{c}}
② 
======================

지금 당장 필요한 것은, 오답 선택지를 채우는 것이다. [중요!] 정답 선택지와 길이만 유사할 뿐 충분히 달라야 한다. (똑같은 단어로 시작하는 것은 금지)
오답 선택지를 만들기 위해 영어지문에 사용된 어휘를 사용할 수는 있지만, 영어지문 내용과 부분적으로 일치하는 것이 오답이 되어서는 안된다. (복수정답 방지)
다른 설명 없이, 네가 만든 오답 문장을(번호 제외) 출력하라.
문장이 아니므로 첫단어도 소문자로 써라.""",

    "constxx": """영어 지문을 읽고 글의 주제를 파악해서 고르는 삼지선다형 객관식 문제를 만들려고 한다. 지금 현재 준비된 것은 다음과 같다.

======================
다음 글의 주제로 가장 적절한 것은?
{{p}}

① {{c}}
② {{w}}
③
======================

지금 당장 필요한 것은, 딱 하나 남은 오답 선택지를 채우는 것이다. [중요!] 다른 선택지와 충분히 달라야 한다. (똑같은 단어로 시작하는 것은 금지)
오답 선택지를 만들기 위해 영어지문에 사용된 어휘를 사용할 수는 있지만, 영어지문 내용과 부분적으로 일치하는 것이 오답이 되어서는 안된다. (복수정답 방지)
다른 설명 없이, 네가 만든 남은 하나의 오답 문장을(번호 제외)  출력하라.
문장이 아니므로 첫단어도 소문자로 써라.""",

    "constyy": """영어 지문을 읽고 글의 주제를 파악해서 고르는 사지선다형 객관식 문제를 만들려고 한다. 지금 현재 준비된 것은 다음과 같다.

======================
다음 글의 주제로 가장 적절한 것은?
{{p}}

① {{c}}
② {{w}}
③ {{x}}
④
======================

지금 당장 필요한 것은, 딱 하나 남은 오답 선택지를 채우는 것이다. [중요!] 다른 선택지와 충분히 달라야 한다. (똑같은 단어로 시작하는 것은 금지)
오답 선택지를 만들기 위해 영어지문에 사용된 어휘를 사용할 수는 있지만, 영어지문 내용과 부분적으로 일치하는 것이 오답이 되어서는 안된다. (복수정답 방지)
다른 설명 없이, 네가 만든 남은 하나의 오답 문장을(번호 제외)  출력하라.
문장이 아니므로 첫단어도 소문자로 써라.""",

    "constzz": """영어 지문을 읽고 글의 주제를 파악해서 고르는 오지선다형 객관식 문제를 만들려고 한다. 지금 현재 준비된 것은 다음과 같다.

======================
다음 글의 주제로 가장 적절한 것은?
{{p}}

① {{c}}
② {{w}}
③ {{x}}
④ {{y}}
⑤
======================

지금 당장 필요한 것은, 딱 하나 남은 오답 선택지를 채우는 것이다. [중요!] 다른 선택지와 충분히 달라야 한다. (똑같은 단어로 시작하는 것은 금지) 
오답 선택지를 만들기 위해 영어지문에 사용된 어휘를 사용할 수는 있지만, 영어지문 내용과 부분적으로 일치하는 것이 오답이 되어서는 안된다. (복수정답 방지)
다른 설명 없이, 네가 만든 남은 하나의 오답 문장을(번호 제외)  출력하라.
문장이 아니므로 첫단어도 소문자로 써라.""",

    "constee": """다음 영어지문의 주제를 파악하는 문제의 해설을 작성해야 한다. 다른 설명은 하지말고 아래 예시의 포맷에 맞추어 주어진 문제를 풀고 그에 대한 해설을 작성해 출력하라.

===포맷===
정답: 원숫자
한국어 해설
[정답 해석] 정답 선택지의 한국어 번역
[오답 해석] 오답 번호 오답 선택지의 한국어 번역 (차례대로)
===예시===
정답: ⑤
자신을 과대평가 또는 과소평가하지 말고 객관적으로 평가하라는 내용의 글이다. 따라서, 글의 주제는 ⑤가 가장 적절하다.
[정답 해석] ⑤ 인생에서 자신의 강점과 약점을 정확하게 평가하는 것의 중요성
[오답 해석] ① 디지털 정보 접근성에서 장애인 고려 부족 ② 정보 접근성과 데이터 분석 효율성 ③ 웹 페이지 접근성 및 정보 획득의 중요성 ④ 건축 설계의 핵심 고려 사항
===네가 해설을 만들어야할 문제===
{{p}}"""
}),


    "constccc": """영어 지문을 읽고 글의 제목을 파악해서 고르는 객관식 문제를 만들려고 한다. 지금 현재 준비된 것은 다음과 같다.

======================
다음 글의 제목으로 가장 적절한 것은?
{{p}}

①
②
③
④
⑤
======================

지금 당장 필요한 것은, 정답 선택지를 만드는 것이다. 정답 선택지는 지문의 요지를 담아내는 제목이야 한다. 다른 설명 없이, 네가 만든 정답 선택지에 들어갈 영어 제목을 (번호 제외) 출력하라.

===예시===
Are Selfies Just a Temporary Trend in Art History?
Fantasy or Reality: Your Selfie Is Not the Real You
The Selfie: A Symbol of Self-oriented Global Culture
The End of Self-portraits: How Selfies Are Taking Over
Selfies, the Latest Innovation in Representing Ourselves
""",

    "constwww": """영어 지문을 읽고 글의 제목을 파악해서 고르는 이지선다형 객관식 문제를 만들려고 한다. 지금 현재 준비된 것은 다음과 같다.

======================
다음 글의 제목으로 가장 적절한 것은?
{{p}}

① {{c}}
② 
======================

지금 당장 필요한 것은, 오답 선택지를 채우는 것이다. [중요!] 정답 선택지와 길이만 유사할 뿐 충분히 달라야 한다. (똑같은 단어로 시작하는 것은 금지)
오답 선택지를 만들기 위해 영어지문에 사용된 어휘를 사용할 수는 있지만, 영어지문 내용과 부분적으로 일치하는 것이 오답이 되어서는 안된다. (복수정답 방지)
다른 설명 없이, 네가 만든 오답 제목을(번호 제외) 출력하라.
""",

    "constxxx": """영어 지문을 읽고 글의 제목를 파악해서 고르는 삼지선다형 객관식 문제를 만들려고 한다. 지금 현재 준비된 것은 다음과 같다.

======================
다음 글의 제목으로 가장 적절한 것은?
{{p}}

① {{c}}
② {{w}}
③
======================

지금 당장 필요한 것은, 딱 하나 남은 오답 선택지를 채우는 것이다. [중요!] 다른 선택지와 충분히 달라야 한다. (똑같은 단어로 시작하는 것은 금지)
오답 선택지를 만들기 위해 영어지문에 사용된 어휘를 사용할 수는 있지만, 영어지문 내용과 부분적으로 일치하는 것이 오답이 되어서는 안된다. (복수정답 방지)
다른 설명 없이, 네가 만든 남은 하나의 오답 제목을(번호 제외)  출력하라.
""",

    "constyyy": """영어 지문을 읽고 글의 제목를 파악해서 고르는 사지선다형 객관식 문제를 만들려고 한다. 지금 현재 준비된 것은 다음과 같다.

======================
다음 글의 제목으로 가장 적절한 것은?
{{p}}

① {{c}}
② {{w}}
③ {{x}}
④
======================

지금 당장 필요한 것은, 딱 하나 남은 오답 선택지를 채우는 것이다. [중요!] 다른 선택지와 충분히 달라야 한다. (똑같은 단어로 시작하는 것은 금지)
오답 선택지를 만들기 위해 영어지문에 사용된 어휘를 사용할 수는 있지만, 영어지문 내용과 부분적으로 일치하는 것이 오답이 되어서는 안된다. (복수정답 방지)
다른 설명 없이, 네가 만든 남은 하나의 오답 제목을(번호 제외)  출력하라.
""",

    "constzzz": """영어 지문을 읽고 글의 제목을 파악해서 고르는 오지선다형 객관식 문제를 만들려고 한다. 지금 현재 준비된 것은 다음과 같다.

======================
다음 글의 제목으로 가장 적절한 것은?
{{p}}

① {{c}}
② {{w}}
③ {{x}}
④ {{y}}
⑤
======================

지금 당장 필요한 것은, 딱 하나 남은 오답 선택지를 채우는 것이다. [중요!] 다른 선택지와 충분히 달라야 한다. (똑같은 단어로 시작하는 것은 금지) 
오답 선택지를 만들기 위해 영어지문에 사용된 어휘를 사용할 수는 있지만, 영어지문 내용과 부분적으로 일치하는 것이 오답이 되어서는 안된다. (복수정답 방지)
다른 설명 없이, 네가 만든 남은 하나의 오답 제목을(번호 제외)  출력하라.
""",

    "consteee": """다음 영어지문의 제목을 파악하는 문제의 해설을 작성해야 한다. 다른 설명은 하지말고 아래 예시의 포맷에 맞추어 주어진 문제를 풀고 그에 대한 해설을 작성해 출력하라.

===포맷===
정답: 원숫자
한국어 해설
[정답 해석] 정답 선택지의 한국어 번역
[오답 해석] 오답 번호 오답 선택지의 한국어 번역 (차례대로)
===예시===
정답: ⑤
자신을 과대평가 또는 과소평가하지 말고 객관적으로 평가하라는 내용의 글이다. 따라서, 글의 제목은 ⑤가 가장 적절하다.
[정답 해석] ⑤ 인생에서 약점파악이 왜 중요한가?
[오답 해석] ① 디지털 정보 접근성: 여전히 소외된 장애인 ② 정보 접근성과 데이터 분석 효율성 ③ 웹 페이지 접근성 및 정보 획득이 가장 중요하다 ④ 건축 설계의 핵심 고려 사항들
===네가 해설을 만들어야할 문제===
{{p}}"""
}

