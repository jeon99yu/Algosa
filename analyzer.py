import json
import re
from openai import OpenAI
from config import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)

def analyze_reviews(reviews):
    text = "\n".join(reviews[:100])  # 리뷰가 많으면 최대 100개만 샘플링

    prompt = f"""
    아래 리뷰들을 분석해 주세요:

    {text}

    출력은 반드시 아래 JSON 형식만 반환하세요.
    다른 설명 문장은 절대 포함하지 마세요.

    {{
        "positive": "긍정 %",
        "neutral": "중립 %",
        "negative": "부정 %",
        "summary": "전체 리뷰 요약",
        "keywords": ["키워드1", "키워드2", "키워드3"],
        "top_positive": ["긍정 리뷰 요약1", "긍정 리뷰 요약2", "긍정 리뷰 요약3"],
        "top_negative": ["부정 리뷰 요약1", "부정 리뷰 요약2", "부정 리뷰 요약3"],
        "common_opinion": "구매자들이 공통적으로 언급한 내용을 토대로 어떤 구매자들이 구매하면 좋을지 추천해줘"
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

        # 순수 JSON만 추출
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
            "keywords": [],
            "top_positive": [],
            "top_negative": [],
            "common_opinion": ""
        }
