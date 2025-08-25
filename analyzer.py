import json
import re
import logging
from openai import OpenAI
from config import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)

def summarize_reviews(reviews, sample_size=50):
    """
    리뷰 리스트를 받아서 전체적인 평가 요약을 JSON 형태로 반환
    - positive_negative: 긍정/부정 의견 핵심
    - features: 자주 언급된 특징
    - cautions: 소비자가 주의해야 할 점
    """
    text = "\n".join(reviews[:sample_size])

    prompt = f"""
    다음은 어떤 상품에 대한 리뷰 모음입니다.
    이를 읽고 다음 항목에 따라 요약하세요.
    - positive_negative: 긍정/부정 핵심의견을 통한 전반적인 평가를 구체적으로 해주세요.
    - features: 자주 언급되는 제품의 장점 3가지
    - cautions: 소비자들이 주의해야 할 점 3가지

    리뷰:
    {text}

    반드시 아래 JSON 형식으로만 출력하세요. 다른 설명은 하지 마세요.
    {{
        "positive_negative": "긍/부정 의견 핵심 요약",
        "features": ["특징1", "특징2", "특징3"],
        "cautions": ["주의사항1", "주의사항2" ,"주의사항3"]
    }}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful review analysis assistant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=600
        )
        content = response.choices[0].message.content.strip()

        match = re.search(r"\{.*\}", content, re.S)
        if match:
            content = match.group()

        return json.loads(content)

    except Exception as e:
        logging.error(f"요약 분석 실패: {e}")
        return {
            "positive_negative": "⚠️ 요약 실패",
            "features": [],
            "cautions": []
        }
