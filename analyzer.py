# analyzer.py
import json
import re
import logging
from openai import OpenAI
from config import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)

def analyze_reviews(reviews, sample_size=100):
    """
    리뷰 리스트를 받아서 LLM으로 분석 → JSON 반환
    """
    text = "\n".join(reviews[:sample_size])

    prompt = f"""
    Please analyze the reviews below:

    {text}

    The output must be returned only in the JSON format below.
    Never include other explanations.
    And TOP_POSITIVE and TOP_NEGATIVE are the most mentioned contents and show them like practical reviews.

    {{
        "positive": "긍정 %",
        "neutral": "중립 %",
        "negative": "부정 %",
        "summary": "전체 리뷰 요약",
        "keywords": ["키워드1", "키워드2", "키워드3"],
        "top_positive": ["긍정 리뷰 요약 1", "긍정 리뷰 요약 2", "긍정 리뷰 요약 3"],
        "top_negative": ["부정 리뷰 요약 1", "부정 리뷰 요약 2", "부정 리뷰 요약 3"],
        "common_opinion": "구매자들이 공통적으로 언급한 점을 기반으로 구매 시 참고할 만한 조언"
    }}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=600
        )
        content = response.choices[0].message["content"].strip()

        # JSON 블록만 추출
        match = re.search(r"\{.*\}", content, re.S)
        if match:
            content = match.group()

        # 문자열 정리
        content = content.strip().strip("`")

        return json.loads(content)

    except Exception as e:
        logging.error(f"리뷰 분석 실패: {e}")
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
