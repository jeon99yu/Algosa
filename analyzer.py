import json
import re
from openai import OpenAI
from config import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)

def analyze_reviews(reviews):
    text = "\n".join(reviews[:50])  # 리뷰가 많으면 일부만 샘플링
    prompt = f"""
    아래 리뷰들을 분석해 주세요:

    {text}

    출력은 반드시 아래 JSON 형식만 반환하세요. 다른 설명 문장은 절대 포함하지 마세요.

    {{
        "positive": "긍정 %",
        "neutral": "중립 %",
        "negative": "부정 %",
        "summary": "요약 텍스트",
        "keywords": ["키워드1", "키워드2", "키워드3"]
    }}
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    try:
        content = response.choices[0].message.content
        if isinstance(content, list):
            content = "".join([c["text"] for c in content if "text" in c])
        content = content.strip()

        print("LLM raw output:", content)  # 디버깅용

        # 순수 JSON만 추출 (혹시 앞뒤에 문장이 붙은 경우 대비)
        match = re.search(r"\{.*\}", content, re.S)
        if match:
            return json.loads(match.group())

        return json.loads(content)

    except Exception as e:
        print("JSON 파싱 실패:", e)
        return {
            "positive": "0%",
            "neutral": "0%",
            "negative": "0%",
            "summary": "분석 실패",
            "keywords": []
        }
